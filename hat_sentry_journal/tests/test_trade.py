from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestTrade(TransactionCase):
    def setUp(self):
        super().setUp()
        self.USD = self.env.ref("base.USD")
        self.Asset = self.env["hat_sentry.asset"]
        self.Trade = self.env["hat_sentry.trade"]
        self.DecisionLog = self.env["hat_sentry.decision.log"]
        self.JournalTag = self.env["hat_sentry.journal.tag"]

        self.asset = self.Asset.sudo().create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.asset.currency_id = self.USD

    def test_create_buy_trade_default_state_open(self):
        trade = self.Trade.create(
            {
                "name": "Test Buy",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 1.0,
                "entry_price": 100.0,
            }
        )
        self.assertEqual(trade.state, "open")
        self.assertEqual(trade.direction, "buy")

    def test_close_trade_computes_pnl(self):
        trade = self.Trade.create(
            {
                "name": "PnL Test",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 2.0,
                "entry_price": 100.0,
                "exit_price": 150.0,
                "total_fees": 10.0,
                "state": "closed",
            }
        )
        self.assertEqual(trade.realized_pnl, 90.0)

    def test_pnl_formula_buy(self):
        trade = self.Trade.create(
            {
                "name": "Buy PnL",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 2.0,
                "entry_price": 100.0,
                "exit_price": 150.0,
                "total_fees": 10.0,
                "state": "closed",
            }
        )
        self.assertAlmostEqual(trade.realized_pnl, 90.0)

    def test_pnl_formula_sell(self):
        trade = self.Trade.create(
            {
                "name": "Sell PnL",
                "asset_id": self.asset.id,
                "direction": "sell",
                "quantity": 1.0,
                "entry_price": 100.0,
                "exit_price": 80.0,
                "total_fees": 2.0,
                "state": "closed",
            }
        )
        self.assertAlmostEqual(trade.realized_pnl, 18.0)

    def test_pnl_zero_when_not_closed(self):
        trade = self.Trade.create(
            {
                "name": "Open Trade",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 1.0,
                "entry_price": 100.0,
                "exit_price": 150.0,
                "state": "open",
            }
        )
        self.assertEqual(trade.realized_pnl, 0.0)
        self.assertEqual(trade.realized_pnl_pct, 0.0)

    def test_pnl_zero_when_no_exit_price(self):
        trade = self.Trade.create(
            {
                "name": "No Exit",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 1.0,
                "entry_price": 100.0,
                "state": "closed",
            }
        )
        self.assertEqual(trade.realized_pnl, 0.0)

    def test_create_decision_log_with_tags(self):
        tag1 = self.JournalTag.create({"name": "Good Entry", "color": 1})
        tag2 = self.JournalTag.create({"name": "High Conviction", "color": 2})
        log = self.DecisionLog.create(
            {
                "name": "Test Decision",
                "asset_id": self.asset.id,
                "decision_type": "entry",
                "thesis": "Bullish on BTC",
                "tag_ids": [(4, tag1.id), (4, tag2.id)],
            }
        )
        self.assertEqual(log.decision_type, "entry")
        self.assertIn(tag1, log.tag_ids)
        self.assertIn(tag2, log.tag_ids)

    def test_create_journal_tag(self):
        tag = self.JournalTag.create({"name": "Test Tag", "color": 5})
        self.assertEqual(tag.name, "Test Tag")
        self.assertTrue(tag.active)

    def test_create_sell_trade_default_state_open(self):
        trade = self.Trade.create(
            {
                "name": "Test Sell",
                "asset_id": self.asset.id,
                "direction": "sell",
                "quantity": 0.5,
                "entry_price": 200.0,
            }
        )
        self.assertEqual(trade.state, "open")
        self.assertEqual(trade.direction, "sell")

    def test_trade_security_trader_can_create(self):
        group_trader = self.env.ref("hat_sentry.group_hat_sentry_trader")
        group_user = self.env.ref("base.group_user")
        user_trader = self.env["res.users"].create(
            {
                "name": "Trader",
                "login": "trader_test",
                "password": "test123",
                "group_ids": [(4, group_trader.id), (4, group_user.id)],
            }
        )
        trade = self.Trade.with_user(user_trader).create(
            {
                "name": "Trader Trade",
                "asset_id": self.asset.id,
                "direction": "buy",
                "quantity": 1.0,
            }
        )
        self.assertEqual(trade.create_uid, user_trader)

    def test_trade_security_user_cannot_create(self):
        group_user = self.env.ref("hat_sentry.group_hat_sentry_user")
        user_user = self.env["res.users"].create(
            {
                "name": "User",
                "login": "user_test",
                "password": "test123",
                "group_ids": [(4, group_user.id)],
            }
        )
        with self.assertRaises(AccessError):
            self.Trade.with_user(user_user).create(
                {
                    "name": "User Trade",
                    "asset_id": self.asset.id,
                    "direction": "buy",
                    "quantity": 1.0,
                }
            )
