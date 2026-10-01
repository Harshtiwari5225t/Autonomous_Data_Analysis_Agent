import streamlit as st
import os
import json
import pandas as pd

from helper import load_data, generate_recommended_questions
from orchestrator import run_agent


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Autonomous Data Analysis Agent",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# TITLE & DESCRIPTION
# --------------------------------------------------

st.title("📊 Autonomous Data Analysis Agent")

st.markdown(
    """
An **Agentic AI-based data analysis system**.
Upload a dataset (CSV, Excel, JSON) and ask any analytical question in plain English.
    """
)


# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=["csv", "xlsx", "xls", "json"]
)


# --------------------------------------------------
# PROCESS FILE
# --------------------------------------------------

if uploaded_file is not None:

    os.makedirs(
        "data/uploads",
        exist_ok=True
    )

    file_path = os.path.join(
        "data/uploads",
        uploaded_file.name
    )

    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    st.success(f"File uploaded: `{uploaded_file.name}`")

    # Load dataset sample for dynamic question recommendations
    try:
        df_sample = load_data(file_path)
        rec_questions = generate_recommended_questions(df_sample)
    except Exception:
        rec_questions = [
            "What is the average discounted_price?",
            "Which categories have the highest average rating?",
            "Find the top 10 products based on rating count"
        ]

    # Initialize session state for user question if not set
    if "selected_question" not in st.session_state:
        st.session_state["selected_question"] = ""

    # --------------------------------------------------
    # RECOMMENDED QUESTIONS BUTTONS
    # --------------------------------------------------

    st.markdown("### 💡 Recommended Questions for Your Dataset")
    st.caption("Click any recommended question below to select it as your query:")
    
    q_cols = st.columns(len(rec_questions))
    for idx, q_text in enumerate(rec_questions):
        if q_cols[idx].button(f"📌 {q_text}", key=f"rec_btn_{idx}"):
            st.session_state["selected_question"] = q_text
            st.rerun()

    # Question text area bound to session state
    question = st.text_area(
        "Ask a question about your dataset",
        value=st.session_state.get("selected_question", ""),
        placeholder="Example: What is the average discounted_price?",
        key="question_input"
    )

    # Synchronize manual edits back to session state
    st.session_state["selected_question"] = question

    # --------------------------------------------------
    # ANALYZE BUTTON
    # --------------------------------------------------

    if st.button("🚀 Analyze Data", type="primary"):

        if not question.strip():
            st.warning("Please enter or select a question.")
        else:
            with st.spinner("Analyzing your dataset with Autonomous Agent..."):
                try:
                    result = run_agent(
                        file_path,
                        question
                    )

                    st.success("Analysis completed!")

                    # ----------------------------------
                    # DATASET & CLEANING SUMMARY
                    # ----------------------------------
                    st.subheader("📌 Overview & Data Quality")
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Rows", result["dataset"]["rows"])
                    m2.metric("Columns", result["dataset"]["columns"])
                    m3.metric("Duplicates Removed", result["data_cleaning"]["duplicates_removed"])
                    m4.metric("Missing Values Cleaned", result["data_cleaning"]["missing_values_before"] - result["data_cleaning"]["missing_values_after"])

                    # ----------------------------------
                    # AI INSIGHT
                    # ----------------------------------
                    st.subheader("💡 Key Insight")
                    st.info(result.get("insight", "No insight generated."))

                    # ----------------------------------
                    # ANALYSIS DETAILS & VISUALIZATION
                    # ----------------------------------
                    st.subheader("📊 Analysis Results")

                    analysis_res = result.get("analysis_result", {})

                    # Check if result contains tabular row items
                    rows_list = None
                    if "result" in analysis_res and isinstance(analysis_res["result"], list):
                        rows_list = analysis_res["result"]
                    elif "result_sample" in analysis_res and isinstance(analysis_res["result_sample"], list):
                        rows_list = analysis_res["result_sample"]

                    if rows_list is not None:
                        if len(rows_list) == 1:
                            # Single row result: Render clean card format (NO unreadable giant metrics, NO table, NO chart)
                            st.markdown("#### 🎯 Result Details")
                            single_row = rows_list[0]
                            
                            # Identify primary title/name field if present
                            title_field = None
                            for name_candidate in ["product_name", "title", "name", "category", "item_name"]:
                                if name_candidate in single_row and single_row[name_candidate]:
                                    title_field = name_candidate
                                    break

                            if title_field:
                                title_val = str(single_row[title_field])
                                st.markdown(f"""
                                <div style="background-color: #f8f9fa; padding: 14px 18px; border-radius: 8px; border-left: 5px solid #0d6efd; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                    <span style="font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #6c757d; font-weight: bold;">{title_field.replace('_', ' ').title()}</span>
                                    <div style="font-size: 17px; font-weight: 600; color: #212529; margin-top: 4px; word-wrap: break-word; line-height: 1.4;">{title_val}</div>
                                </div>
                                """, unsafe_allow_html=True)

                            # Separate numeric metrics and text fields
                            num_fields = {k: v for k, v in single_row.items() if k != title_field and isinstance(v, (int, float))}
                            text_fields = {k: v for k, v in single_row.items() if k != title_field and not isinstance(v, (int, float))}

                            # Render numeric metrics in badge columns
                            if num_fields:
                                m_cols = st.columns(min(len(num_fields), 4))
                                for idx, (k, v) in enumerate(num_fields.items()):
                                    field_label = k.replace("_", " ").title()
                                    formatted_val = f"{v:,.2f}" if isinstance(v, float) else f"{v:,}"
                                    m_cols[idx % len(m_cols)].metric(field_label, formatted_val)

                            # Render text fields in clean formatted markdown blocks
                            if text_fields:
                                for k, v in text_fields.items():
                                    if v is not None and str(v).strip():
                                        field_label = k.replace("_", " ").title()
                                        st.markdown(f"**{field_label}:** {v}")

                        elif len(rows_list) > 1:
                            # Multiple rows: Display interactive Dataframe Table
                            res_df = pd.DataFrame(rows_list)
                            st.dataframe(res_df, use_container_width=True)

                            # Render Chart only when there are multiple data points (> 1 row)
                            chart_data = analysis_res.get("chart_data")
                            if chart_data and "data" in chart_data and len(chart_data["data"]) > 1:
                                st.subheader("📈 Visualization")
                                chart_df = pd.DataFrame(chart_data["data"])
                                if "x" in chart_df.columns and "y" in chart_df.columns:
                                    chart_df = chart_df.set_index("x")
                                    st.bar_chart(chart_df["y"], use_container_width=True)

                    elif "result" in analysis_res:
                        # Scalar result (e.g. average, sum, count, min, max, correlation)
                        op_name = analysis_res.get('operation', 'metric').replace("_", " ").title()
                        val = analysis_res['result']
                        st.markdown("#### 🎯 Result Summary")
                        if isinstance(val, float):
                            st.metric(op_name, f"{val:,.2f}")
                        elif isinstance(val, int):
                            st.metric(op_name, f"{val:,}")
                        else:
                            st.write(f"**{op_name}:** {val}")

                    # ----------------------------------
                    # RAW JSON DETAILS & DOWNLOAD
                    # ----------------------------------
                    with st.expander("🔍 Detailed Agent Response (JSON)"):
                        st.json(result)

                    json_data = json.dumps(
                        result,
                        indent=4,
                        default=str
                    )

                    st.download_button(
                        label="📥 Download JSON Report",
                        data=json_data,
                        file_name="analysis_result.json",
                        mime="application/json"
                    )

                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")