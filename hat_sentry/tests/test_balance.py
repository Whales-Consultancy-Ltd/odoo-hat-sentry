from odoo.tests.common import TransactionCase


class TestBalance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Asset = self.env["hat_sentry.asset"]
        self.Snapshot = self.env["hat_sentry.portfolio.snapshot"]
        self.Balance = self.env["hat_sentry.balance"]
        self.asset = self.Asset.create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.snapshot = self.Snapshot.create({"total_value": 10000.0})

    def test_create_balance(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "free_amount": 1.5,
                "locked_amount": 0.5,
                "price_usdt": 50000.0,
            }
        )
        self.assertEqual(bal.free_amount, 1.5)
        self.assertEqual(bal.locked_amount, 0.5)

    def test_total_amount_is_free_plus_locked(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "free_amount": 2.0,
                "locked_amount": 1.0,
            }
        )
        self.assertAlmostEqual(bal.total_amount, 3.0)

    def test_display_name_format(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "account_type": "spot",
            }
        )
        expected = f"[{self.snapshot.id}] BTC - spot"
        self.assertEqual(bal.display_name, expected)

    def test_account_type_spot(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "account_type": "spot",
            }
        )
        self.assertEqual(bal.account_type, "spot")

    def test_account_type_futures(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "account_type": "futures",
            }
        )
        self.assertEqual(bal.account_type, "futures")

    def test_account_type_earn(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "account_type": "earn",
            }
        )
        self.assertEqual(bal.account_type, "earn")

    def test_relation_to_snapshot(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
            }
        )
        self.assertEqual(bal.snapshot_id, self.snapshot)

    def test_relation_to_asset(self):
        bal = self.Balance.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
            }
        )
        self.assertEqual(bal.asset_id, self.asset)
