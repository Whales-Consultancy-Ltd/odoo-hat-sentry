from odoo.tests.common import TransactionCase


class TestEarnPosition(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Asset = self.env["hat_sentry.asset"]
        self.Snapshot = self.env["hat_sentry.portfolio.snapshot"]
        self.Earn = self.env["hat_sentry.earn.position"]
        self.asset = self.Asset.create(
            {
                "symbol": "ETH",
                "asset_type": "crypto",
                "bucket": "passive_income",
            }
        )
        self.snapshot = self.Snapshot.create({"total_value": 10000.0})

    def test_create_earn_position(self):
        earn = self.Earn.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "product_type": "flexible",
                "amount": 2.5,
                "apy": 5.5,
            }
        )
        self.assertEqual(earn.amount, 2.5)
        self.assertEqual(earn.apy, 5.5)
        self.assertEqual(earn.product_type, "flexible")

    def test_create_locked_earn_position(self):
        earn = self.Earn.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "product_type": "locked",
                "amount": 10.0,
                "apy": 12.0,
            }
        )
        self.assertEqual(earn.product_type, "locked")

    def test_earn_position_relation_to_asset(self):
        earn = self.Earn.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "product_type": "flexible",
            }
        )
        self.assertEqual(earn.asset_id, self.asset)

    def test_earn_position_relation_to_snapshot(self):
        earn = self.Earn.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "product_type": "flexible",
            }
        )
        self.assertEqual(earn.snapshot_id, self.snapshot)

    def test_earn_position_display_name(self):
        earn = self.Earn.create(
            {
                "snapshot_id": self.snapshot.id,
                "asset_id": self.asset.id,
                "product_type": "flexible",
            }
        )
        self.assertEqual(earn.display_name, "ETH (Flexible)")
