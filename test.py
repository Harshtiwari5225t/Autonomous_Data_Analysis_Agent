import unittest
import os
import pandas as pd
import numpy as np

from helper import (
    load_data,
    profile_data,
    clean_data,
    get_statistics,
    get_column_information,
    _clean_numeric_series
)
from orchestrator import (
    call_gemini_with_retry,
    analyze_dataset,
    execute_analysis,
    generate_insight,
    run_agent,
    parse_llm_json
)


class Test1GeminiConnectivity(unittest.TestCase):
    """Test Gemini LLM connectivity and retry wrapper."""

    def test_gemini_connection(self):
        response = call_gemini_with_retry("Say 'Hello from Test' in one word.")
        self.assertIsNotNone(response)
        self.assertTrue(len(response) > 0)


class Test2HelperFunctions(unittest.TestCase):
    """Test data loading, profiling, cleaning, and statistics helpers."""

    def test_numeric_cleaning_currency_and_percent(self):
        s = pd.Series(["₹1,299", "$450.50", "64%", "invalid_|", None])
        cleaned = _clean_numeric_series(s)
        self.assertEqual(cleaned[0], 1299.0)
        self.assertEqual(cleaned[1], 450.50)
        self.assertEqual(cleaned[2], 64.0)
        self.assertTrue(pd.isna(cleaned[3]))

    def test_clean_data(self):
        raw_df = pd.DataFrame({
            " product_name ": ["Item A", "Item B", "Item A"],
            " discounted_price ": ["₹399", "₹1,099", "₹399"],
            " rating ": ["4.2", "|", "4.2"]
        })
        cleaned_df, report = clean_data(raw_df)

        # Check column name space stripping
        self.assertIn("product_name", cleaned_df.columns)
        self.assertIn("discounted_price", cleaned_df.columns)
        self.assertIn("rating", cleaned_df.columns)

        # Check duplicate removal
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(len(cleaned_df), 2)

        # Check numeric conversions
        self.assertTrue(pd.api.types.is_numeric_dtype(cleaned_df["discounted_price"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(cleaned_df["rating"]))

    def test_profile_data(self):
        df = pd.DataFrame({
            "col_a": [1, 2, 3],
            "col_b": ["x", "y", "z"]
        })
        profile = profile_data(df)
        self.assertEqual(profile["rows"], 3)
        self.assertEqual(profile["columns"], 2)
        self.assertEqual(profile["column_names"], ["col_a", "col_b"])

    def test_get_statistics(self):
        df = pd.DataFrame({
            "price": [100.0, 200.0, 300.0]
        })
        stats = get_statistics(df)
        self.assertIn("price", stats)
        self.assertEqual(stats["price"]["mean"], 200.0)
        self.assertEqual(stats["price"]["min"], 100.0)
        self.assertEqual(stats["price"]["max"], 300.0)


class Test3OrchestratorOperations(unittest.TestCase):
    """Test analytical execution logic in orchestrator."""

    def setUp(self):
        self.df = pd.DataFrame({
            "product_name": ["Prod A", "Prod B", "Prod C", "Prod D", "Prod E"],
            "category": ["Electronics", "Electronics", "Home", "Home", "Home"],
            "discounted_price": [100.0, 200.0, 300.0, 400.0, 500.0],
            "rating": [4.0, 4.5, 4.2, 4.8, 5.0],
            "rating_count": [1000, 5000, 2000, 8000, 10000]
        })

    def test_parse_llm_json(self):
        json_str = '```json\n{"operation": "average", "column": "discounted_price"}\n```'
        parsed = parse_llm_json(json_str)
        self.assertEqual(parsed["operation"], "average")
        self.assertEqual(parsed["column"], "discounted_price")

    def test_execute_average(self):
        plan = {"operation": "average", "column": "discounted_price"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "average")
        self.assertEqual(res["result"], 300.0)

    def test_execute_sum(self):
        plan = {"operation": "sum", "column": "discounted_price"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "sum")
        self.assertEqual(res["result"], 1500.0)

    def test_execute_min_max(self):
        plan_min = {"operation": "minimum", "column": "discounted_price"}
        res_min = execute_analysis(self.df, plan_min)
        self.assertEqual(res_min["result"], 100.0)

        plan_max = {"operation": "maximum", "column": "discounted_price"}
        res_max = execute_analysis(self.df, plan_max)
        self.assertEqual(res_max["result"], 500.0)

    def test_execute_top_n(self):
        plan = {"operation": "top_n", "column": "rating_count", "n": 3, "ascending": False}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "top_n")
        self.assertEqual(len(res["result"]), 3)
        self.assertEqual(res["result"][0]["product_name"], "Prod E")

    def test_execute_group_by(self):
        plan = {"operation": "group_by", "group_column": "category", "target_column": "rating", "agg": "average"}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "group_by")
        self.assertEqual(len(res["result"]), 2)

    def test_execute_filter(self):
        plan = {"operation": "filter", "column": "discounted_price", "condition": ">", "value": 250.0}
        res = execute_analysis(self.df, plan)
        self.assertEqual(res["operation"], "filter")
        self.assertEqual(res["matching_count"], 3)


class Test4FullAgentIntegration(unittest.TestCase):
    """Integration test running full agent pipeline on dataset."""

    def test_run_agent_integration(self):
        dataset_path = "data/uploads/amazon.csv"
        if os.path.exists(dataset_path):
            result = run_agent(dataset_path, "What is the average discounted_price?")
            self.assertEqual(result["status"], "success")
            self.assertIn("analysis_plan", result)
            self.assertIn("analysis_result", result)
            self.assertIn("insight", result)
            self.assertTrue(len(result["insight"]) > 0)


if __name__ == "__main__":
    unittest.main()
