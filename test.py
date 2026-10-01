import unittest
import os
import sys
import tempfile
import warnings
import logging
import pandas as pd
import numpy as np

# Suppress non-critical warnings in test runner
warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)
os.environ["STREAMLIT_SUPPRESS_MESSAGES"] = "true"

from helper import (
    load_data,
    profile_data,
    clean_data,
    get_statistics,
    get_column_information,
    _clean_numeric_series,
    generate_recommended_questions
)
from orchestrator import (
    call_gemini_with_retry,
    analyze_dataset,
    execute_analysis,
    generate_insight,
    run_agent,
    parse_llm_json
)


class Test1HelperFunctions(unittest.TestCase):
    """Unit tests for dataset loading, numeric cleaning, profiling, and statistics (helper.py)."""

    def test_load_csv_data(self):
        dataset_path = "data/uploads/amazon.csv"
        if os.path.exists(dataset_path):
            df = load_data(dataset_path)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertGreater(len(df), 0)

    def test_load_json_data(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write('[{"id": 1, "price": 100}, {"id": 2, "price": 200}]')
            temp_name = f.name

        try:
            df = load_data(temp_name)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 2)
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    def test_load_excel_xlsx_data(self):
        df_orig = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            temp_name = f.name
        
        try:
            df_orig.to_excel(temp_name, index=False)
            df_loaded = load_data(temp_name)
            self.assertIsInstance(df_loaded, pd.DataFrame)
            self.assertEqual(len(df_loaded), 2)
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    def test_load_unsupported_format(self):
        with self.assertRaises(ValueError):
            load_data("invalid_file.txt")

    def test_numeric_cleaning_currency_and_percent(self):
        s = pd.Series(["₹1,299", "$450.50", "64%", "invalid_|", None])
        cleaned = _clean_numeric_series(s)
        self.assertEqual(cleaned[0], 1299.0)
        self.assertEqual(cleaned[1], 450.50)
        self.assertEqual(cleaned[2], 64.0)
        self.assertTrue(pd.isna(cleaned[3]))

    def test_numeric_cleaning_float_series(self):
        s = pd.Series([10.5, 20.0, 30.25])
        cleaned = _clean_numeric_series(s)
        self.assertEqual(cleaned.tolist(), [10.5, 20.0, 30.25])

    def test_numeric_cleaning_int_series(self):
        s = pd.Series([1, 2, 3])
        cleaned = _clean_numeric_series(s)
        self.assertEqual(cleaned.tolist(), [1, 2, 3])

    def test_numeric_cleaning_negative_numbers(self):
        s = pd.Series(["-₹150.00", "-$45.50", "100.0"])
        cleaned = _clean_numeric_series(s)
        self.assertEqual(cleaned[0], -150.0)
        self.assertEqual(cleaned[1], -45.50)

    def test_numeric_cleaning_scientific_notation(self):
        s = pd.Series(["1.5e3", "2.0e-1"])
        cleaned = _clean_numeric_series(s)
        self.assertEqual(cleaned[0], 1500.0)
        self.assertEqual(cleaned[1], 0.2)

    def test_numeric_cleaning_text_column(self):
        s = pd.Series(["Product A", "Product B", "Product C"])
        cleaned = _clean_numeric_series(s)
        self.assertEqual(cleaned[0], "Product A")
        self.assertEqual(cleaned[1], "Product B")

    def test_clean_data_duplicates_and_whitespace(self):
        raw_df = pd.DataFrame({
            " product_name ": ["Item A", "Item B", "Item A"],
            " discounted_price ": ["₹399", "₹1,099", "₹399"],
            " rating ": ["4.2", "|", "4.2"]
        })
        cleaned_df, report = clean_data(raw_df)

        self.assertIn("product_name", cleaned_df.columns)
        self.assertIn("discounted_price", cleaned_df.columns)
        self.assertIn("rating", cleaned_df.columns)
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(len(cleaned_df), 2)
        self.assertTrue(pd.api.types.is_numeric_dtype(cleaned_df["discounted_price"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(cleaned_df["rating"]))

    def test_clean_data_missing_values_imputation(self):
        raw_df = pd.DataFrame({
            "val": [10.0, np.nan, 30.0],
            "cat": ["A", None, "A"]
        })
        cleaned_df, report = clean_data(raw_df)
        self.assertEqual(cleaned_df["val"].iloc[1], 20.0)  # Median
        self.assertEqual(cleaned_df["cat"].iloc[1], "A")   # Mode

    def test_clean_data_no_duplicates(self):
        raw_df = pd.DataFrame({
            "x": [1, 2, 3],
            "y": ["a", "b", "c"]
        })
        cleaned_df, report = clean_data(raw_df)
        self.assertEqual(report["duplicates_removed"], 0)
        self.assertEqual(len(cleaned_df), 3)

    def test_clean_data_all_missing_numeric(self):
        raw_df = pd.DataFrame({
            "val": [np.nan, np.nan, np.nan],
            "cat": ["A", "B", "C"]
        })
        cleaned_df, report = clean_data(raw_df)
        self.assertEqual(cleaned_df["val"].tolist(), [0.0, 0.0, 0.0])

    def test_clean_data_empty_dataframe(self):
        raw_df = pd.DataFrame()
        cleaned_df, report = clean_data(raw_df)
        self.assertEqual(len(cleaned_df), 0)
        self.assertEqual(report["rows_before"], 0)

    def test_profile_data_with_missing_and_duplicates(self):
        df = pd.DataFrame({
            "col_a": [1, None, 1],
            "col_b": ["x", "y", "x"]
        })
        profile = profile_data(df)
        self.assertEqual(profile["rows"], 3)
        self.assertEqual(profile["columns"], 2)
        self.assertEqual(profile["duplicate_rows"], 1)
        self.assertEqual(profile["missing_values"]["col_a"], 1)

    def test_profile_data_zero_missing(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        profile = profile_data(df)
        self.assertEqual(profile["missing_values"], {})
        self.assertEqual(profile["duplicate_rows"], 0)

    def test_get_statistics_numeric(self):
        df = pd.DataFrame({
            "price": [100.0, 200.0, 300.0]
        })
        stats = get_statistics(df)
        self.assertIn("price", stats)
        self.assertEqual(stats["price"]["mean"], 200.0)
        self.assertEqual(stats["price"]["min"], 100.0)
        self.assertEqual(stats["price"]["max"], 300.0)

    def test_get_statistics_empty_numeric(self):
        df = pd.DataFrame({"text": ["a", "b", "c"]})
        stats = get_statistics(df)
        self.assertEqual(stats, {})

    def test_get_column_information(self):
        df = pd.DataFrame({
            "col1": [1, 2, 2],
            "col2": ["a", None, "b"]
        })
        info = get_column_information(df)
        self.assertIn("col1", info)
        self.assertEqual(info["col1"]["unique_values"], 2)
        self.assertEqual(info["col2"]["missing_values"], 1)


class Test2OrchestratorOperations(unittest.TestCase):
    """Unit tests for analytical execution operations and JSON parsing (orchestrator.py)."""

    def setUp(self):
        self.df = pd.DataFrame({
            "product_name": ["Prod A", "Prod B", "Prod C", "Prod D", "Prod E"],
            "category": ["Electronics", "Electronics", "Home", "Home", "Home"],
            "discounted_price": [100.0, 200.0, 300.0, 400.0, 500.0],
            "rating": [4.0, 4.5, 4.2, 4.8, 5.0],
            "rating_count": [1000, 5000, 2000, 8000, 10000]
        })

    def test_parse_llm_json_standard(self):
        json_str = '{"operation": "average", "column": "discounted_price"}'
        parsed = parse_llm_json(json_str)
        self.assertEqual(parsed["operation"], "average")
        self.assertEqual(parsed["column"], "discounted_price")

    def test_parse_llm_json_markdown_block(self):
        json_str = '```json\n{"operation": "average", "column": "discounted_price"}\n```'
        parsed = parse_llm_json(json_str)
        self.assertEqual(parsed["operation"], "average")
        self.assertEqual(parsed["column"], "discounted_price")

    def test_parse_llm_json_uppercase_markdown(self):
        json_str = '```JSON\n{"operation": "count"}\n```'
        parsed = parse_llm_json(json_str)
        self.assertEqual(parsed["operation"], "count")

    def test_parse_llm_json_with_extra_text(self):
        json_str = 'Here is the plan: {"operation": "count"} thanks'
        parsed = parse_llm_json(json_str)
        self.assertEqual(parsed["operation"], "count")

    def test_parse_llm_json_invalid_raises_error(self):
        with self.assertRaises(Exception):
            parse_llm_json("No JSON content here")

    def test_execute_average(self):
        plan = {"operation": "average", "column": "discounted_price"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "average")
        self.assertEqual(res["result"], 300.0)

    def test_execute_average_case_insensitive_column(self):
        plan = {"operation": "average", "column": "DISCOUNTED_PRICE"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["result"], 300.0)

    def test_execute_average_all_nans(self):
        df_nan = pd.DataFrame({"price": [np.nan, np.nan]})
        plan = {"operation": "average", "column": "price"}
        res = execute_analysis(df_nan, plan)
        self.assertEqual(res["result"], 0.0)

    def test_execute_sum(self):
        plan = {"operation": "sum", "column": "discounted_price"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "sum")
        self.assertEqual(res["result"], 1500.0)

    def test_execute_sum_all_nans(self):
        df_nan = pd.DataFrame({"price": [np.nan, np.nan]})
        plan = {"operation": "sum", "column": "price"}
        res = execute_analysis(df_nan, plan)
        self.assertEqual(res["result"], 0.0)

    def test_execute_minimum_numeric(self):
        plan = {"operation": "minimum", "column": "discounted_price"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["result"], 100.0)

    def test_execute_minimum_string(self):
        df_str = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        plan = {"operation": "minimum", "column": "name"}
        res = execute_analysis(df_str, plan)
        self.assertEqual(res["result"], "Alice")

    def test_execute_maximum_numeric(self):
        plan = {"operation": "maximum", "column": "discounted_price"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["result"], 500.0)

    def test_execute_maximum_string(self):
        df_str = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        plan = {"operation": "maximum", "column": "name"}
        res = execute_analysis(df_str, plan)
        self.assertEqual(res["result"], "Charlie")

    def test_execute_count(self):
        plan = {"operation": "count"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "count")
        self.assertEqual(res["result"], 5)

    def test_execute_describe(self):
        plan = {"operation": "describe"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "describe")
        self.assertIn("discounted_price", res["result"])

    def test_execute_top_n_multi_rows_descending(self):
        plan = {"operation": "top_n", "column": "rating_count", "n": 3, "ascending": False}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "top_n")
        self.assertEqual(len(res["result"]), 3)
        self.assertEqual(res["result"][0]["product_name"], "Prod E")

    def test_execute_top_n_single_row(self):
        plan = {"operation": "top_n", "column": "rating_count", "n": 1, "ascending": False}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "top_n")
        self.assertEqual(len(res["result"]), 1)
        self.assertEqual(res["result"][0]["product_name"], "Prod E")

    def test_execute_top_n_ascending_true(self):
        plan = {"operation": "top_n", "column": "rating_count", "n": 2, "ascending": True}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["result"][0]["product_name"], "Prod A")

    def test_execute_top_n_missing_display_columns(self):
        df_simple = pd.DataFrame({"item": ["X", "Y"], "score": [10, 20]})
        plan = {"operation": "top_n", "column": "score", "n": 1, "ascending": False}
        res = execute_analysis(df_simple, plan)
        self.assertEqual(res["result"][0]["item"], "Y")

    def test_execute_group_by_average(self):
        plan = {"operation": "group_by", "group_column": "category", "target_column": "rating", "agg": "average"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "group_by")
        self.assertEqual(len(res["result"]), 2)
        self.assertIn("chart_data", res)

    def test_execute_group_by_sum(self):
        plan = {"operation": "group_by", "group_column": "category", "target_column": "discounted_price", "agg": "sum"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["result"][0]["category"], "Home")
        self.assertEqual(res["result"][0]["discounted_price"], 1200.0)

    def test_execute_group_by_count(self):
        plan = {"operation": "group_by", "group_column": "category", "target_column": "product_name", "agg": "count"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["result"][0]["category"], "Home")
        self.assertEqual(res["result"][0]["product_name"], 3)

    def test_execute_group_by_invalid_agg_fallback(self):
        plan = {"operation": "group_by", "group_column": "category", "target_column": "rating", "agg": "invalid_agg"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "group_by")
        self.assertEqual(len(res["result"]), 2)

    def test_execute_filter_greater_than(self):
        plan = {"operation": "filter", "column": "discounted_price", "condition": ">", "value": 250.0}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "filter")
        self.assertEqual(res["matching_count"], 3)

    def test_execute_filter_less_than(self):
        plan = {"operation": "filter", "column": "discounted_price", "condition": "<", "value": 250.0}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "filter")
        self.assertEqual(res["matching_count"], 2)

    def test_execute_filter_greater_equal(self):
        plan = {"operation": "filter", "column": "discounted_price", "condition": ">=", "value": 300.0}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["matching_count"], 3)

    def test_execute_filter_less_equal(self):
        plan = {"operation": "filter", "column": "discounted_price", "condition": "<=", "value": 300.0}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["matching_count"], 3)

    def test_execute_filter_equal(self):
        plan = {"operation": "filter", "column": "discounted_price", "condition": "==", "value": 300.0}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["matching_count"], 1)

    def test_execute_filter_no_matches(self):
        plan = {"operation": "filter", "column": "discounted_price", "condition": ">", "value": 1000.0}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["matching_count"], 0)
        self.assertEqual(len(res["result_sample"]), 0)

    def test_execute_correlation(self):
        plan = {"operation": "correlation", "column1": "discounted_price", "column2": "rating"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "correlation")
        self.assertIsInstance(res["result"], float)

    def test_execute_correlation_constant_column(self):
        df_const = pd.DataFrame({"a": [1, 2, 3], "b": [5, 5, 5]})
        plan = {"operation": "correlation", "column1": "a", "column2": "b"}
        res = execute_analysis(df_const, plan)
        self.assertEqual(res["result"], 0.0)

    def test_execute_unknown_operation_fallback(self):
        plan = {"operation": "custom_operation"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "custom_operation")


class Test3RecommendedQuestionGenerator(unittest.TestCase):
    """Unit tests for recommended question generator (helper.py)."""

    def test_generate_recommended_questions_standard(self):
        df = pd.DataFrame({
            "product_name": ["A", "B"],
            "category": ["X", "Y"],
            "discounted_price": [100, 200],
            "rating": [4.0, 4.5],
            "rating_count": [50, 100],
            "discount_percentage": [10, 20]
        })
        questions = generate_recommended_questions(df)
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)
        self.assertIn("What is the average discounted_price?", questions)

    def test_generate_recommended_questions_no_price_column(self):
        df = pd.DataFrame({
            "title": ["Item A", "Item B"],
            "rating": [4.0, 5.0]
        })
        questions = generate_recommended_questions(df)
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)

    def test_generate_recommended_questions_single_column(self):
        df = pd.DataFrame({"sales": [10, 20, 30]})
        questions = generate_recommended_questions(df)
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)

    def test_generate_recommended_questions_empty_df(self):
        df = pd.DataFrame()
        questions = generate_recommended_questions(df)
        self.assertIsInstance(questions, list)
        self.assertGreater(len(questions), 0)


class Test4GeminiLLMConnectivity(unittest.TestCase):
    """Integration tests for Gemini LLM calls and retry handling."""

    def test_gemini_connection(self):
        try:
            response = call_gemini_with_retry("Say 'Hello from Test' in one word.")
            self.assertIsNotNone(response)
            self.assertTrue(len(response) > 0)
        except Exception as e:
            if any(k in str(e) for k in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                self.skipTest(f"Gemini API rate limit or high demand: {e}")
            else:
                raise e

    def test_analyze_dataset_llm_planning(self):
        df = pd.DataFrame({
            "discounted_price": [100, 200, 300],
            "rating": [4.0, 4.5, 5.0]
        })
        try:
            plan = analyze_dataset(df, "What is the average discounted_price?")
            self.assertIn("operation", plan)
        except Exception as e:
            if any(k in str(e) for k in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                self.skipTest(f"Gemini API rate limit or high demand: {e}")
            else:
                raise e

    def test_generate_insight_llm(self):
        analysis_result = {"operation": "average", "column": "discounted_price", "result": 200.0}
        try:
            insight = generate_insight("What is the average discounted_price?", analysis_result)
            self.assertIsInstance(insight, str)
            self.assertGreater(len(insight), 0)
        except Exception as e:
            if any(k in str(e) for k in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                self.skipTest(f"Gemini API rate limit or high demand: {e}")
            else:
                raise e


class Test5FullAgentIntegration(unittest.TestCase):
    """End-to-end integration test running full agent pipeline on dataset."""

    def test_run_agent_integration_amazon(self):
        dataset_path = "data/uploads/amazon.csv"
        if os.path.exists(dataset_path):
            try:
                result = run_agent(dataset_path, "What is the average discounted_price?")
                self.assertEqual(result["status"], "success")
                self.assertIn("data_cleaning", result)
                self.assertIn("column_information", result)
                self.assertIn("analysis_plan", result)
                self.assertIn("analysis_result", result)
                self.assertIn("insight", result)
                self.assertTrue(len(result["insight"]) > 0)
            except Exception as e:
                if any(k in str(e) for k in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"]):
                    self.skipTest(f"Gemini API rate limit or high demand: {e}")
                else:
                    raise e

    def test_run_agent_invalid_file_path(self):
        with self.assertRaises(Exception):
            run_agent("non_existent_file.csv", "What is the average price?")


if __name__ == "__main__":
    unittest.main(verbosity=2)