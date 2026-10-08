import os
import sys
import tempfile
import unittest
import pandas as pd
import numpy as np

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.execution.validator import validate_code_ast
from app.execution.sandbox import execute_pandas_code_safely
from app.services.report_service import report_service
from app.services.profiling_service import profiling_service
from app.graph.nodes.code_generator import code_generator_node
from app.graph.nodes.visualization import visualization_node
from app.graph.nodes.insights import insights_node
from app.graph.state import AnalysisState


class TestASTValidator(unittest.TestCase):
    def test_forbidden_imports_blocked(self):
        unsafe_snippets = [
            "import os\nresult = 1",
            "import sys\nresult = 1",
            "import subprocess\nresult = 1",
            "import multiprocessing\nresult = 1",
            "import sqlite3\nresult = 1",
            "from pathlib import Path\nresult = 1"
        ]
        for snippet in unsafe_snippets:
            is_valid, errors = validate_code_ast(snippet)
            self.assertFalse(is_valid, f"Expected '{snippet}' to be rejected")
            self.assertTrue(len(errors) > 0)

    def test_forbidden_builtins_blocked(self):
        unsafe_snippets = [
            "f = open('test.txt', 'w')\nresult = 1",
            "eval('1 + 1')\nresult = 1",
            "exec('a = 1')\nresult = 1",
            "__import__('os').system('dir')\nresult = 1"
        ]
        for snippet in unsafe_snippets:
            is_valid, errors = validate_code_ast(snippet)
            self.assertFalse(is_valid, f"Expected '{snippet}' to be rejected")

    def test_file_io_methods_blocked(self):
        unsafe_snippets = [
            "df.to_csv('out.csv')\nresult = df",
            "df.to_excel('out.xlsx')\nresult = df",
            "pd.read_csv('secrets.csv')\nresult = 1",
            "pd.read_sql('SELECT * FROM users', conn)\nresult = 1"
        ]
        for snippet in unsafe_snippets:
            is_valid, errors = validate_code_ast(snippet)
            self.assertFalse(is_valid, f"Expected '{snippet}' to be rejected")

    def test_sandbox_introspection_blocked(self):
        unsafe_snippets = [
            "result = df.__class__.__subclasses__()",
            "result = df.__mro__",
            "result = df.__globals__"
        ]
        for snippet in unsafe_snippets:
            is_valid, errors = validate_code_ast(snippet)
            self.assertFalse(is_valid, f"Expected '{snippet}' to be rejected")

    def test_valid_pandas_code_allowed(self):
        safe_snippets = [
            "result = df.groupby('Region', as_index=False)['Sales'].sum().sort_values('Sales', ascending=False)",
            "result = df['Sales'].mean()",
            "df['Order Date'] = pd.to_datetime(df['Order Date'])\nresult = df[df['Order Date'].dt.year == 2025]"
        ]
        for snippet in safe_snippets:
            is_valid, errors = validate_code_ast(snippet)
            self.assertTrue(is_valid, f"Expected safe code to be allowed, got errors: {errors}")


class TestSandboxExecution(unittest.TestCase):
    def setUp(self):
        self.tmp_csv = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        self.tmp_csv.write("Region,Category,Sales,Profit,Candidate\nEast,Tech,100,20,Alice\nWest,Office,200,40,Bob\n")
        self.tmp_csv.close()

    def tearDown(self):
        if os.path.exists(self.tmp_csv.name):
            os.remove(self.tmp_csv.name)

    def test_safe_execution_success(self):
        code = "result = df.groupby('Region', as_index=False)['Sales'].sum()"
        success, res_dict, err = execute_pandas_code_safely(self.tmp_csv.name, code, timeout_seconds=10)
        self.assertTrue(success, f"Execution failed: {err}")
        self.assertEqual(res_dict.get("type"), "dataframe")
        self.assertEqual(len(res_dict.get("data", [])), 2)

    def test_unsafe_execution_rejected_before_worker(self):
        code = "import os\nresult = df"
        success, res_dict, err = execute_pandas_code_safely(self.tmp_csv.name, code)
        self.assertFalse(success)
        self.assertIn("Security Validation Failed", err)


class TestReportLabXMLEscaping(unittest.TestCase):
    def test_special_characters_in_pdf_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            orig_reports_dir = sys.modules['app.core.config'].settings.REPORTS_DIR
            sys.modules['app.core.config'].settings.REPORTS_DIR = tmp_dir
            try:
                # Content with special characters: <, >, &, quotes
                pdf_path = report_service.generate_pdf_report(
                    workspace_name="AT&T Sales & Strategy <Q2>",
                    workspace_id="test_ws",
                    report_name="Revenue > 1000 & Profit < 200 Analysis",
                    saved_insights=[{"content": "Sales & Profit grew by > 15% where Discount < 0.1"}],
                    analyses=[{"question": "Is Sales > 500 & Cost < 300?", "insights": "Derived: High growth & margin > 25%."}],
                    dataset_info={"filename": "sales & metrics.csv", "row_count": 100, "column_count": 5, "quality_score": 98.5}
                )
                self.assertTrue(os.path.exists(pdf_path))
                self.assertTrue(os.path.getsize(pdf_path) > 0)
            finally:
                sys.modules['app.core.config'].settings.REPORTS_DIR = orig_reports_dir


class TestCodeGeneratorFallback(unittest.TestCase):
    def test_fallback_without_numeric_columns_no_name_error(self):
        # Empty numeric columns should never crash with NameError: name 'df' is not defined
        state = {
            "dataset_profile": {
                "columns": [{"name": "Status", "data_type": "string"}, {"name": "Description", "data_type": "string"}]
            },
            "user_query": "Summarize status",
            "gemini_api_key": ""
        }
        res = code_generator_node(state)
        self.assertIn("generated_code", res)
        self.assertTrue(len(res["generated_code"]) > 0)


class TestVisualizationMultiMetric(unittest.TestCase):
    def test_multi_metric_traces_generated(self):
        state = {
            "execution_result": {
                "type": "dataframe",
                "columns": ["Region", "Sales", "Profit"],
                "data": [
                    {"Region": "East", "Sales": 1000, "Profit": 300},
                    {"Region": "West", "Sales": 1500, "Profit": 450}
                ]
            }
        }
        res = visualization_node(state)
        chart = res.get("chart_config")
        self.assertIsNotNone(chart)
        spec = chart.get("spec", {})
        data = spec.get("data", [])
        # Should generate 2 traces for Sales and Profit
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Sales")
        self.assertEqual(data[1]["name"], "Profit")


class TestDateDetectionHeuristic(unittest.TestCase):
    def test_substring_words_not_falsely_flagged_as_dates(self):
        tmp_csv = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        tmp_csv.write("candidate_id,update_flag,order_date,amount\n101,1,2025-01-01,100\n102,0,2025-01-02,200\n")
        tmp_csv.close()
        try:
            profile = profiling_service.profile_dataset(tmp_csv.name, "test.csv")
            date_cols = profile.get("semantic_summary", {}).get("time_dimensions", [])
            self.assertIn("order_date", date_cols)
            self.assertNotIn("candidate_id", date_cols)
            self.assertNotIn("update_flag", date_cols)
        finally:
            if os.path.exists(tmp_csv.name):
                os.remove(tmp_csv.name)


class TestInsightsStructure(unittest.TestCase):
    def test_insights_node_returns_structured_sections(self):
        state: AnalysisState = {
            "question": "What are the total orders in 2023?",
            "result_table": [
                {"year": 2023, "total_orders": 30, "avg_daily_orders": 1}
            ],
            "result_summary": {
                "shape": (1, 3),
                "columns": ["year", "total_orders", "avg_daily_orders"],
                "data": [{"year": 2023, "total_orders": 30, "avg_daily_orders": 1}]
            }
        }
        res = insights_node(state)
        # Check that the 3 required sections from user photo are returned
        self.assertIn("key_findings", res)
        self.assertIn("data_interpretation", res)
        self.assertIn("strategic_recommendations", res)

        key_findings = res["key_findings"]
        self.assertIsInstance(key_findings, list)
        self.assertTrue(len(key_findings) > 0)
        for kf in key_findings:
            self.assertIn("title", kf)
            self.assertIn("description", kf)

        data_interp = res["data_interpretation"]
        self.assertIsInstance(data_interp, str)
        self.assertTrue(len(data_interp) > 0)

        strategic_recs = res["strategic_recommendations"]
        self.assertIsInstance(strategic_recs, list)
        self.assertTrue(len(strategic_recs) > 0)
        for rec in strategic_recs:
            self.assertIn("title", rec)
            self.assertIn("description", rec)

        # Backward compatibility fields
        self.assertIn("insights", res)
        self.assertIn("recommendations", res)
        self.assertIn("follow_up_questions", res)


class TestMultiColumnCombinations(unittest.TestCase):
    def setUp(self):
        self.tmp_csv = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8")
        self.tmp_csv.write(
            "Region,Category,Sales,Profit\n"
            "East,Tech,1000,200\n"
            "East,Furniture,500,50\n"
            "West,Tech,1200,250\n"
            "West,Furniture,600,70\n"
        )
        self.tmp_csv.close()

    def tearDown(self):
        if os.path.exists(self.tmp_csv.name):
            os.remove(self.tmp_csv.name)

    def test_multi_column_groupby_preserves_dimensions_in_sandbox(self):
        # Even without as_index=False, the sandbox worker must reset index and preserve all columns
        code = "result = df.groupby(['Region', 'Category'])[['Sales', 'Profit']].sum()"
        success, res_dict, err = execute_pandas_code_safely(self.tmp_csv.name, code)
        self.assertTrue(success, f"Execution failed: {err}")
        self.assertEqual(res_dict.get("type"), "dataframe")
        columns = res_dict.get("columns", [])
        self.assertIn("Region", columns)
        self.assertIn("Category", columns)
        self.assertIn("Sales", columns)
        self.assertIn("Profit", columns)

        data = res_dict.get("data", [])
        self.assertEqual(len(data), 4)
        for row in data:
            self.assertIn("Region", row)
            self.assertIn("Category", row)
            self.assertIn("Sales", row)
            self.assertIn("Profit", row)

    def test_two_dimensions_one_metric_grouped_bar_chart(self):
        state = {
            "execution_result": {
                "type": "dataframe",
                "columns": ["Region", "Category", "Sales"],
                "data": [
                    {"Region": "East", "Category": "Tech", "Sales": 1000},
                    {"Region": "East", "Category": "Furniture", "Sales": 500},
                    {"Region": "West", "Category": "Tech", "Sales": 1200},
                    {"Region": "West", "Category": "Furniture", "Sales": 600}
                ]
            }
        }
        res = visualization_node(state)
        chart = res.get("chart_config")
        self.assertIsNotNone(chart)
        spec = chart.get("spec", {})
        data = spec.get("data", [])
        # Should generate grouped traces for Tech and Furniture
        self.assertEqual(len(data), 2)
        trace_names = {t["name"] for t in data}
        self.assertEqual(trace_names, {"Tech", "Furniture"})
        self.assertEqual(spec.get("layout", {}).get("barmode"), "group")

    def test_multi_column_code_generator_fallback(self):
        state = {
            "dataset_profile": {
                "columns": [
                    {"name": "Region", "data_type": "string"},
                    {"name": "Category", "data_type": "string"},
                    {"name": "Sales", "data_type": "float"},
                    {"name": "Profit", "data_type": "float"}
                ]
            },
            "user_query": "Show total sales and profit by Region and Category",
            "gemini_api_key": ""
        }
        res = code_generator_node(state)
        code = res.get("generated_code", "")
        self.assertIn("Region", code)
        self.assertIn("Category", code)
        self.assertIn("Sales", code)
        self.assertIn("groupby", code)

    def test_multi_column_insights_reporting(self):
        state: AnalysisState = {
            "user_query": "Sales by Region and Category",
            "result_table": [
                {"Region": "East", "Category": "Tech", "Sales": 1000},
                {"Region": "West", "Category": "Furniture", "Sales": 600}
            ],
            "result_summary": "DataFrame with 2 rows"
        }
        res = insights_node(state)
        key_findings = res.get("key_findings", [])
        self.assertTrue(len(key_findings) > 0)
        top_finding = key_findings[0]
        # Must report combination "East - Tech" and not mistake "Tech" for the metric value
        self.assertIn("East - Tech", top_finding["title"])
        self.assertIn("1000", top_finding["description"])


if __name__ == "__main__":
    unittest.main()


