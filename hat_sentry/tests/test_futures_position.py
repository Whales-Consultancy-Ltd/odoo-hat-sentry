from odoo.tests.common import TransactionCase


class TestFuturesPosition(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Snapshot = self.env["hat_sentry.portfolio.snapshot"]
        self.Position = self.env["hat_sentry.futures.position"]
        self.snapshot = self.Snapshot.create({"total_value": 10000.0})

    def test_create_long_position(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "long",
                "entry_price": 50000.0,
                "mark_price": 52000.0,
                "position_size": 0.1,
                "liquidation_price": 45000.0,
            }
        )
        self.assertEqual(pos.symbol, "BTCUSDT")
        self.assertEqual(pos.side, "long")
        self.assertEqual(pos.state, "open")

    def test_liq_distance_long(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "long",
                "entry_price": 50000.0,
                "mark_price": 52000.0,
                "liquidation_price": 48000.0,
            }
        )
        expected = ((52000.0 - 48000.0) / 48000.0) * 100
        self.assertAlmostEqual(pos.distance_to_liquidation_pct, expected, places=2)

    def test_liq_distance_short(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "short",
                "entry_price": 50000.0,
                "mark_price": 48000.0,
                "liquidation_price": 53000.0,
            }
        )
        expected = ((53000.0 - 48000.0) / 48000.0) * 100
        self.assertAlmostEqual(pos.distance_to_liquidation_pct, expected, places=2)

    def test_liq_distance_zero_when_no_liquidation_price(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "long",
                "entry_price": 50000.0,
                "mark_price": 52000.0,
            }
        )
        self.assertEqual(pos.distance_to_liquidation_pct, 0.0)

    def test_has_stop_loss_true_when_set(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "long",
                "stop_loss_price": 49000.0,
            }
        )
        self.assertTrue(pos.has_stop_loss)

    def test_has_stop_loss_false_when_zero(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "long",
            }
        )
        self.assertFalse(pos.has_stop_loss)

    def test_display_name_format(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "long",
            }
        )
        self.assertEqual(pos.display_name, "BTCUSDT (long)")

    def test_default_state_is_open(self):
        pos = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "ETHUSDT",
                "side": "short",
            }
        )
        self.assertEqual(pos.state, "open")
