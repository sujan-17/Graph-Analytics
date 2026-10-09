import os
import sys
import unittest
import tempfile

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.dataset_analyst_service import dataset_analyst_service
from app.services.report_service import report_service

class TestDataAnalystReportModule(unittest.TestCase):
    def test_analyst_report_structure_and_no_chat_queries(self):
        sample_path = os.path.join(backend_dir, "storage", "sample_sales.csv")
        rep = dataset_analyst_service.generate_analyst_report(
            sample_path,
            "sample_sales.csv",
            "Executive Dataset Analysis"
        )
        # 1. Verification of Core Data Analyst Pillars
        self.assertIn("executive_summary", rep)
        self.assertIn("what_data_is_analysed", rep)
        self.assertIn("what_dataset_depicts", rep)
        self.assertIn("what_can_be_done", rep)

        # 2. Verification that no chat history or user queries are included
        self.assertNotIn("chat_history", rep)
        self.assertNotIn("user_query", rep)
        self.assertNotIn("user_queries", rep)
        self.assertNotIn("analyses_history", rep)

        # 3. What data is analysed details
        what_analysed = rep["what_data_is_analysed"]
        self.assertTrue(len(what_analysed.get("numeric_metrics", [])) > 0)
        self.assertTrue(len(what_analysed.get("categorical_dimensions", [])) > 0)

        # 4. What dataset depicts details
        what_depicts = rep["what_dataset_depicts"]
        self.assertTrue(len(what_depicts.get("key_patterns", [])) > 0)

        # 5. What can be done details
        what_can_be_done = rep["what_can_be_done"]
        self.assertTrue(len(what_can_be_done.get("strategic_actions", [])) > 0)
        self.assertTrue(len(what_can_be_done.get("advanced_analytics", [])) > 0)

        # 6. PDF Report compilation
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = report_service.generate_pdf_report(
                workspace_name="Test Enterprise Workspace",
                workspace_id="test_ws_id",
                report_name="Executive Dataset Analysis",
                analyst_report=rep
            )
            self.assertTrue(os.path.exists(pdf_path))
            self.assertTrue(os.path.getsize(pdf_path) > 1000)

if __name__ == "__main__":
    unittest.main()
