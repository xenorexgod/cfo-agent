import unittest

from tests.test_calculations import load_sample_data

from cfo_agent.reports import REPORTS, render_report


class ReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_data = load_sample_data()

    def test_all_reports_render(self) -> None:
        for name in REPORTS:
            content = render_report(name, self.sample_data)
            self.assertTrue(content.startswith("# "))
            self.assertIn("Suits Workspaces", content)

    def test_daily_cash_report_contains_free_cash(self) -> None:
        content = render_report("daily_cash", self.sample_data)
        self.assertIn("Free usable cash", content)
        self.assertIn("INR 4.00 lakh", content)

    def test_unknown_report_raises_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown report"):
            render_report("missing", self.sample_data)


if __name__ == "__main__":
    unittest.main()
