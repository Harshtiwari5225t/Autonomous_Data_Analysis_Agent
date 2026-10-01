import json
import pandas as pd
from dotenv import load_dotenv
import os
import re
import time
import numpy as np

from helper import (
    load_data,
    profile_data,
    clean_data,
    get_statistics,
    get_column_information
)


# --------------------------------------------------
# CUSTOM EXCEPTIONS & CONFIGURATION
# --------------------------------------------------

class AnalysisError(Exception):
    """Custom exception raised when data analysis operation fails."""
    pass


class MissingAPIKeyError(Exception):
    """Custom exception raised when no Gemini API key is configured."""
    pass


DEFAULT_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"]


def get_api_key():
    return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""


def get_models():
    models_env = os.getenv("GEMINI_MODELS")
    if models_env:
        return [m.strip() for m in models_env.split(",") if m.strip()]
    return DEFAULT_MODELS


def get_client():
    key = get_api_key()
    if not key:
        raise MissingAPIKeyError("No API key configured. Please set GOOGLE_API_KEY or GEMINI_API_KEY in .env.")
    return genai.Client(api_key=key)


# --------------------------------------------------
# LOAD ENVIRONMENT & INITIALIZE CLIENT
# --------------------------------------------------

load_dotenv()

from google import genai

api_key = get_api_key()
client = genai.Client(api_key=api_key) if api_key else None


# --------------------------------------------------
# GEMINI RETRY WRAPPER WITH MODEL FALLBACK & JSON PARSER
# --------------------------------------------------

def call_gemini_with_retry(prompt, config=None, models=["gemini-3.5-flash", "gemini-3.8-flash", "gemini-flash-latest"], max_retries=3):
    """
    Call Gemini API with retry logic and fallback models to handle 503 high demand or 429 quota limits.
    """
    last_exception = None
    for model_name in models:
        for attempt in range(max_retries):
            try:
                if config:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                else:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                return response.text.strip()
            except Exception as e:
                last_exception = e
                err_str = str(e)
                if any(k in err_str for k in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"]):
                    time.sleep(2 ** attempt + 1)
                else:
                    break

    raise last_exception


def parse_llm_json(text):
    """
    Safely extract and parse JSON from LLM output.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


# --------------------------------------------------
# ANALYSIS PLANNING
# --------------------------------------------------

def analyze_dataset(df, question):

    columns = df.columns.tolist()

    prompt = f"""
You are an autonomous data analysis planning agent.

Dataset columns:
{columns}

User question:
{question}

Determine what type of analysis is required.

Allowed operations and JSON schema formats:

1. "average": Mean of a numeric column.
   Format: {{"operation": "average", "column": "column_name"}}

2. "sum": Total sum of a numeric column.
   Format: {{"operation": "sum", "column": "column_name"}}

3. "minimum": Minimum value of a column.
   Format: {{"operation": "minimum", "column": "column_name"}}

4. "maximum": Maximum value of a column.
   Format: {{"operation": "maximum", "column": "column_name"}}

5. "count": Total count of records.
   Format: {{"operation": "count"}}

6. "describe": Summary statistics of dataset.
   Format: {{"operation": "describe"}}

7. "top_n": Top/highest or bottom/lowest N rows sorted by a column.
   Format: {{"operation": "top_n", "column": "column_name", "n": 10, "ascending": false}}

8. "group_by": Category analysis / aggregation by a categorical column.
   Format: {{"operation": "group_by", "group_column": "group_column_name", "target_column": "target_column_name", "agg": "average", "top_n": 10}}

9. "filter": Filter records matching a numerical threshold (>, <, >=, <=, ==).
   Format: {{"operation": "filter", "column": "column_name", "condition": ">", "value": 50}}

10. "correlation": Correlation between two numeric columns.
   Format: {{"operation": "correlation", "column1": "col1", "column2": "col2"}}

Return ONLY valid JSON matching exact dataset column names.
Do NOT use markdown.
Do NOT use ```json.
Do NOT include explanations.
"""

    response_text = call_gemini_with_retry(
        prompt=prompt,
        config={
            "temperature": 0,
            "response_mime_type": "application/json"
        }
    )

    return parse_llm_json(response_text)


# --------------------------------------------------
# EXECUTE ANALYSIS
# --------------------------------------------------

def execute_analysis(df, plan):

    operation = plan.get("operation")
    column = plan.get("column")

    # Match column names case-insensitively if not found directly
    col_map = {c.lower(): c for c in df.columns}

    def resolve_col(c):
        if not c:
            return c
        return col_map.get(str(c).lower(), c)

    column = resolve_col(column)

    if operation == "average":
        value = df[column].mean()
        return {
            "operation": "average",
            "column": column,
            "result": round(float(value), 4) if pd.notnull(value) else 0.0
        }

    elif operation == "sum":
        value = df[column].sum()
        return {
            "operation": "sum",
            "column": column,
            "result": round(float(value), 4) if pd.notnull(value) else 0.0
        }

    elif operation == "minimum":
        value = df[column].min()
        return {
            "operation": "minimum",
            "column": column,
            "result": float(value) if isinstance(value, (int, float, np.number)) else str(value)
        }

    elif operation == "maximum":
        value = df[column].max()
        return {
            "operation": "maximum",
            "column": column,
            "result": float(value) if isinstance(value, (int, float, np.number)) else str(value)
        }

    elif operation == "count":
        return {
            "operation": "count",
            "result": int(len(df))
        }

    elif operation == "describe":
        statistics = get_statistics(df)
        return {
            "operation": "describe",
            "result": statistics
        }

    elif operation == "top_n":
        n = int(plan.get("n", 10))
        ascending = bool(plan.get("ascending", False))
        sorted_df = df.sort_values(by=column, ascending=ascending).head(n)

        display_cols = [c for c in ["product_name", "category", column, "discounted_price", "actual_price", "rating", "rating_count"] if c in df.columns]
        if not any(k in display_cols for k in ["product_name", "category"]) and len(df.columns) > 0:
            display_cols.insert(0, df.columns[0])
        if column not in display_cols:
            display_cols.append(column)
        display_cols = list(dict.fromkeys(display_cols))

        subset = sorted_df[display_cols].replace({np.nan: None})
        records = subset.to_dict(orient="records")

        x_col = "product_name" if "product_name" in subset.columns else subset.columns[0]
        chart_data = {
            "type": "bar",
            "x_label": x_col,
            "y_label": column,
            "data": [
                {"x": str(row[x_col])[:30], "y": float(row[column]) if row[column] is not None and isinstance(row[column], (int, float, np.number)) else 0}
                for row in records
            ]
        }

        return {
            "operation": "top_n",
            "column": column,
            "n": n,
            "result": records,
            "chart_data": chart_data
        }

    elif operation == "group_by":
        group_col = resolve_col(plan.get("group_column"))
        target_col = resolve_col(plan.get("target_column"))
        agg = plan.get("agg", "average")
        top_n = int(plan.get("top_n", 10))

        if agg in ["average", "mean"]:
            grouped = df.groupby(group_col)[target_col].mean().reset_index()
        elif agg == "sum":
            grouped = df.groupby(group_col)[target_col].sum().reset_index()
        elif agg == "count":
            grouped = df.groupby(group_col)[target_col].count().reset_index()
        else:
            grouped = df.groupby(group_col)[target_col].mean().reset_index()

        grouped = grouped.sort_values(by=target_col, ascending=False).head(top_n)
        grouped[target_col] = grouped[target_col].round(2)

        records = grouped.replace({np.nan: None}).to_dict(orient="records")

        chart_data = {
            "type": "bar",
            "x_label": group_col,
            "y_label": target_col,
            "data": [
                {"x": str(row[group_col])[:30], "y": float(row[target_col]) if row[target_col] is not None else 0}
                for row in records
            ]
        }

        return {
            "operation": "group_by",
            "group_column": group_col,
            "target_column": target_col,
            "agg": agg,
            "result": records,
            "chart_data": chart_data
        }

    elif operation == "filter":
        cond = plan.get("condition", ">")
        val = float(plan.get("value", 0))

        if cond == ">":
            filtered_df = df[df[column] > val]
        elif cond == "<":
            filtered_df = df[df[column] < val]
        elif cond == ">=":
            filtered_df = df[df[column] >= val]
        elif cond == "<=":
            filtered_df = df[df[column] <= val]
        else:
            filtered_df = df[df[column] == val]

        display_cols = [c for c in ["product_name", "category", column, "discounted_price", "actual_price", "rating"] if c in df.columns]
        if column not in display_cols:
            display_cols.append(column)
        display_cols = list(dict.fromkeys(display_cols))

        subset = filtered_df.head(20)[display_cols].replace({np.nan: None})
        records = subset.to_dict(orient="records")

        return {
            "operation": "filter",
            "column": column,
            "condition": cond,
            "value": val,
            "matching_count": int(len(filtered_df)),
            "result_sample": records
        }

    elif operation == "correlation":
        col1 = resolve_col(plan.get("column1"))
        col2 = resolve_col(plan.get("column2"))
        corr_val = df[col1].corr(df[col2])
        return {
            "operation": "correlation",
            "column1": col1,
            "column2": col2,
            "result": round(float(corr_val), 4) if pd.notnull(corr_val) else 0.0
        }

    else:
        return {
            "operation": operation,
            "message": "Operation executed with standard metric summaries.",
            "result": get_statistics(df)
        }


# --------------------------------------------------
# GENERATE INSIGHT
# --------------------------------------------------

def generate_insight(question, analysis_result):

    prompt = f"""
User question:
{question}

Analysis result:
{analysis_result}

Explain the result clearly and concisely in two or three sentences.
Highlight key numerical values or key takeaways.
Do not invent any information.
"""

    result = call_gemini_with_retry(
        prompt=prompt
    )

    return result


# --------------------------------------------------
# MAIN AGENT
# --------------------------------------------------

def run_agent(file_path, question):

    # STEP 1: Load data
    df = load_data(file_path)

    # STEP 2: Profile raw dataset
    profile = profile_data(df)

    # STEP 3: Clean dataset
    cleaned_df, cleaning_report = clean_data(df)

    # STEP 4: Get column information
    column_information = get_column_information(
        cleaned_df
    )

    # STEP 5: Ask LLM to create analysis plan
    plan = analyze_dataset(
        cleaned_df,
        question
    )

    # STEP 6: Execute analysis using Python
    analysis_result = execute_analysis(
        cleaned_df,
        plan
    )

    # STEP 7: Generate human-readable insight
    insight = generate_insight(
        question,
        analysis_result
    )

    # STEP 8: Final JSON response
    result = {
        "status": "success",
        "question": question,
        "dataset": {
            "rows": profile["rows"],
            "columns": profile["columns"]
        },
        "data_cleaning": cleaning_report,
        "column_information": column_information,
        "analysis_plan": plan,
        "analysis_result": analysis_result,
        "insight": insight
    }

    return result