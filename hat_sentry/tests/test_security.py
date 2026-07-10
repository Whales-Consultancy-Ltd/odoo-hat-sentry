from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestSecurity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.USD = self.env.ref("base.USD")
        self.main_company = self.env.ref("base.main_company")

        self.group_user = self.env.ref("hat_sentry.group_hat_sentry_user")
        self.group_trader = self.env.ref("hat_sentry.group_hat_sentry_trader")
        self.group_manager = self.env.ref("hat_sentry.group_hat_sentry_manager")

        self.user_user = self._create_user("test_user", self.group_user)
        self.user_trader = self._create_user("test_trader", self.group_trader)
        self.user_manager = self._create_user("test_manager", self.group_manager)

        self.Asset = self.env["hat_sentry.asset"]
        self.Trade = self.env["hat_sentry.trade"]
        self.Snapshot = self.env["hat_sentry.portfolio.snapshot"]

        self.asset = self.Asset.sudo().create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.snapshot = self.Snapshot.sudo().create({"total_value": 10000.0})

    def _create_user(self, login, group):
        return self.env["res.users"].create(
            {
                "name": login.title(),
                "login": login,
                "password": "test123",
                "groups_id": [(4, group.id)],
                "company_id": self.main_company.id,
            }
        )

    # --- User (read-only) ---

    def test_user_can_read_asset(self):
        assets = self.Asset.sudo(self.user_user).search([("id", "=", self.asset.id)])
        self.assertIn(self.asset, assets)

    def test_user_cannot_create_asset(self):
        with self.assertRaises(AccessError):
            self.Asset.sudo(self.user_user).create(
                {
                    "symbol": "ETH",
                    "asset_type": "crypto",
                    "bucket": "trading",
                }
            )

    def test_user_cannot_create_trade(self):
        with self.assertRaises(AccessError):
            self.Trade.sudo(self.user_user).create(
                {
                    "name": "Test Trade",
                    "asset_id": self.asset.id,
                    "direction": "buy",
                    "quantity": 1.0,
                }
            )

    # --- Trader ---

    def test_trader_can_create_trade(self):
        trade = self.Trade.sudo(self.user_trader).create(
            {
                "name": "Trader Trade",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 1.0,
            }
        )
        self.assertTrue(trade)
        self.assertEqual(trade.create_uid, self.user_trader)

    def test_trader_can_read_own_trade(self):
        trade = self.Trade.sudo(self.user_trader).create(
            {
                "name": "Own Trade",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 1.0,
            }
        )
        found = self.Trade.sudo(self.user_trader).search([("id", "=", trade.id)])
        self.assertIn(trade, found)

    def test_trader_cannot_create_asset(self):
        with self.assertRaises(AccessError):
            self.Asset.sudo(self.user_trader).create(
                {
                    "symbol": "ETH",
                    "asset_type": "crypto",
                    "bucket": "trading",
                }
            )

    # --- Manager ---

    def test_manager_can_create_asset(self):
        asset = self.Asset.sudo(self.user_manager).create(
            {
                "symbol": "ETH",
                "asset_type": "crypto",
                "bucket": "trading",
            }
        )
        self.assertTrue(asset)

    def test_manager_can_edit_asset(self):
        self.Asset.sudo(self.user_manager).browse(self.asset.id).write({"name": "Edited"})
        self.assertEqual(self.asset.name, "Edited")

    def test_manager_can_delete_asset(self):
        eth = self.Asset.sudo(self.user_manager).create(
            {
                "symbol": "ETH",
                "asset_type": "crypto",
                "bucket": "trading",
            }
        )
        eth.sudo(self.user_manager).unlink()
        self.assertFalse(self.Asset.search([("id", "=", eth.id)]))

    def test_manager_can_create_trade(self):
        trade = self.Trade.sudo(self.user_manager).create(
            {
                "name": "Manager Trade",
                "asset_id": self.asset.id,
                "direction": "sell",
                "quantity": 0.5,
            }
        )
        self.assertTrue(trade)

    # --- Multi-company isolation ---

    def test_multi_company_asset_isolation(self):
        company_b = self.env["res.company"].sudo().create({"name": "Company B"})
        user_b = self._create_user("user_b", self.group_manager)
        user_b.write({"company_ids": [(4, company_b.id)], "company_id": company_b.id})

        asset_b = self.Asset.sudo().create(
            {
                "symbol": "ETH",
                "asset_type": "crypto",
                "bucket": "trading",
                "company_id": company_b.id,
            }
        )
        assets_for_b = self.Asset.sudo(user_b).search([("id", "=", asset_b.id)])
        self.assertIn(asset_b, assets_for_b)

        assets_for_a = self.Asset.sudo(self.user_user).search([("id", "=", asset_b.id)])
        self.assertNotIn(asset_b, assets_for_a)
