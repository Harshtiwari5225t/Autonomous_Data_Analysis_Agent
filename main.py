import streamlit as st
import os
import json
import pandas as pd

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

    # --------------------------------------------------
    # USER QUESTION & SAMPLE SUGGESTIONS
    # --------------------------------------------------

    st.markdown("### 💡 Example Questions")
    col1, col2, col3 = st.columns(3)

    sample_q = ""
    if col1.button("Average discounted price"):
        sample_q = "What is the average discounted_price?"
    if col2.button("Top rated categories"):
        sample_q = "Which categories have the highest average rating?"
    if col3.button("Top 10 popular products"):
        sample_q = "Find the top 10 products based on rating count"

    question = st.text_area(
        "Ask a question about your dataset",
        value=sample_q if sample_q else "",
        placeholder="Example: What is the average discounted_price?"
    )

    # --------------------------------------------------
    # ANALYZE BUTTON
    # --------------------------------------------------

    if st.button("🚀 Analyze Data", type="primary"):

        if not question.strip():
            st.warning("Please enter a question.")
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

                    # Render Tabular Data if present
                    if "result" in analysis_res and isinstance(analysis_res["result"], list):
                        res_df = pd.DataFrame(analysis_res["result"])
                        st.dataframe(res_df, use_container_width=True)

                    elif "result_sample" in analysis_res and isinstance(analysis_res["result_sample"], list):
                        res_df = pd.DataFrame(analysis_res["result_sample"])
                        st.dataframe(res_df, use_container_width=True)

                    elif "result" in analysis_res:
                        st.write(f"**Result ({analysis_res.get('operation', 'metric')}):**", analysis_res["result"])

                    # Render Chart if chart_data present
                    chart_data = analysis_res.get("chart_data")
                    if chart_data and "data" in chart_data and len(chart_data["data"]) > 0:
                        st.subheader("📈 Visualization")
                        chart_df = pd.DataFrame(chart_data["data"])
                        if "x" in chart_df.columns and "y" in chart_df.columns:
                            chart_df = chart_df.set_index("x")
                            st.bar_chart(chart_df["y"], use_container_width=True)

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