from datetime import datetime

from odoo.tests.common import TransactionCase


class TestPortfolioSnapshot(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Snapshot = self.env["hat_sentry.portfolio.snapshot"]

    def test_create_snapshot_with_values(self):
        snap = self.Snapshot.create(
            {
                "total_value": 50000.0,
                "spot_value": 40000.0,
                "futures_margin_value": 5000.0,
                "futures_notional_value": 2000.0,
                "stablecoin_value": 10000.0,
                "core_value": 20000.0,
                "passive_income_value": 5000.0,
                "experimental_value": 1000.0,
            }
        )
        self.assertTrue(snap.snapshot_datetime)
        self.assertEqual(snap.total_value, 50000.0)

    def test_health_score_default_fifty(self):
        snap = self.Snapshot.create({"total_value": 0.0})
        self.assertEqual(snap.health_score, 50)

    def test_health_score_increases_with_good_metrics(self):
        snap = self.Snapshot.create(
            {
                "total_value": 50000.0,
                "futures_notional_value": 2000.0,
                "stablecoin_value": 10000.0,
                "core_value": 20000.0,
                "passive_income_value": 5000.0,
            }
        )
        self.assertEqual(snap.health_score, 100)

    def test_health_score_decreases_with_high_exposure(self):
        snap = self.Snapshot.create(
            {
                "total_value": 1000.0,
                "futures_notional_value": 900.0,
            }
        )
        self.assertEqual(snap.health_score, 35)

    def test_health_score_never_below_zero(self):
        snap = self.Snapshot.create(
            {
                "total_value": 100.0,
                "futures_notional_value": 100.0,
                "stablecoin_value": 1.0,
            }
        )
        self.assertGreaterEqual(snap.health_score, 0)

    def test_health_score_never_above_one_hundred(self):
        snap = self.Snapshot.create(
            {
                "total_value": 1000.0,
                "futures_notional_value": 10.0,
                "stablecoin_value": 500.0,
                "core_value": 500.0,
                "passive_income_value": 100.0,
            }
        )
        self.assertLessEqual(snap.health_score, 100)

    def test_trading_value_computed(self):
        snap = self.Snapshot.create(
            {
                "total_value": 50000.0,
                "spot_value": 40000.0,
                "core_value": 15000.0,
                "stablecoin_value": 5000.0,
            }
        )
        self.assertEqual(snap.trading_value, 20000.0)

    def test_trading_value_not_negative(self):
        snap = self.Snapshot.create(
            {
                "total_value": 10000.0,
                "spot_value": 1000.0,
                "core_value": 2000.0,
                "stablecoin_value": 1000.0,
            }
        )
        self.assertEqual(snap.trading_value, 0.0)

    def test_total_exposure(self):
        snap = self.Snapshot.create(
            {
                "total_value": 50000.0,
                "futures_notional_value": 10000.0,
            }
        )
        self.assertEqual(snap.total_exposure, 60000.0)

    def test_total_exposure_without_futures(self):
        snap = self.Snapshot.create(
            {
                "total_value": 50000.0,
            }
        )
        self.assertEqual(snap.total_exposure, 50000.0)

    def test_allocation_pcts_sum_to_approx_one_hundred(self):
        snap = self.Snapshot.create(
            {
                "total_value": 10000.0,
                "spot_value": 8500.0,
                "core_value": 2000.0,
                "stablecoin_value": 1000.0,
                "passive_income_value": 500.0,
                "futures_notional_value": 500.0,
                "experimental_value": 500.0,
            }
        )
        total = (
            snap.allocation_core_pct
            + snap.allocation_stable_pct
            + snap.allocation_trading_pct
            + snap.allocation_passive_pct
            + snap.allocation_futures_pct
            + snap.allocation_experimental_pct
        )
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_snapshot_ordering_newest_first(self):
        snap1 = self.Snapshot.create(
            {
                "total_value": 100.0,
                "snapshot_datetime": datetime(2024, 1, 1, 12, 0, 0),
            }
        )
        snap2 = self.Snapshot.create(
            {
                "total_value": 200.0,
                "snapshot_datetime": datetime(2024, 6, 1, 12, 0, 0),
            }
        )
        snaps = self.Snapshot.search([])
        self.assertEqual(snaps[0], snap2)
        self.assertEqual(snaps[-1], snap1)

    def test_multi_company_company_id_assigned(self):
        company_b = self.env["res.company"].create({"name": "Test Company B"})
        snap = self.Snapshot.with_company(company_b).create(
            {
                "total_value": 100.0,
            }
        )
        self.assertEqual(snap.company_id, company_b)
