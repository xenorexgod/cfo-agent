import json
import unittest
from pathlib import Path

from cfo_agent.calculations import (
    cash_runway_days,
    deal_metrics,
    diligence_readiness_score,
    free_usable_cash,
    overdue_receivables,
    receivables_by_bucket,
)
from cfo_agent.models import Deal, FinanceData


def load_sample_data() -> FinanceData:
    path = Path(__file__).resolve().parents[1] / "examples" / "suits_may_2026.json"
    return FinanceData.from_dict(json.loads(path.read_text(encoding="utf-8")))


class CalculationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_data = load_sample_data()

    def test_free_usable_cash(self) -> None:
        self.assertEqual(free_usable_cash(self.sample_data.cash), 400000)
        self.assertEqual(round(cash_runway_days(400000, self.sample_data.cash.monthly_fixed_obligations), 1), 5.5)

    def test_receivables_buckets(self) -> None:
        self.assertEqual(overdue_receivables(self.sample_data.receivables), 1800000)
        buckets = receivables_by_bucket(self.sample_data.receivables)
        self.assertEqual(buckets["1-30"], 450000)
        self.assertEqual(buckets["31-60"], 550000)
        self.assertEqual(buckets["61-90"], 800000)

    def test_deal_metrics_match_cfo_pack(self) -> None:
        deal = Deal(
            client="Test Client Pvt Ltd",
            centre="Suits Workspaces Jaipur",
            seats=25,
            standard_price_per_seat=8000,
            proposed_price_per_seat=6500,
            monthly_operating_cost=87500,
            capex=500000,
            broker_commission=150000,
            lock_in_months=12,
        )
        metrics = deal_metrics(deal)
        self.assertEqual(metrics["proposed_revenue"], 162500)
        self.assertEqual(metrics["monthly_contribution"], 75000)
        self.assertEqual(round(metrics["payback_months"], 1), 8.7)

    def test_diligence_score_is_conditional(self) -> None:
        self.assertEqual(diligence_readiness_score(self.sample_data), 48)


if __name__ == "__main__":
    unittest.main()
