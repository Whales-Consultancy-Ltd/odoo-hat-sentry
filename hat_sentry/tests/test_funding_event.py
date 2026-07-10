from odoo.tests.common import TransactionCase


class TestFundingEvent(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Snapshot = self.env["hat_sentry.portfolio.snapshot"]
        self.Position = self.env["hat_sentry.futures.position"]
        self.FundingEvent = self.env["hat_sentry.funding.event"]
        self.snapshot = self.Snapshot.create({"total_value": 10000.0})
        self.position = self.Position.create(
            {
                "snapshot_id": self.snapshot.id,
                "symbol": "BTCUSDT",
                "side": "long",
            }
        )

    def test_create_funding_event_positive_rate(self):
        event = self.FundingEvent.create(
            {
                "position_id": self.position.id,
                "symbol": "BTCUSDT",
                "funding_rate": 0.01,
                "funding_direction": "paid",
            }
        )
        self.assertEqual(event.funding_rate, 0.01)
        self.assertEqual(event.funding_direction, "paid")

    def test_create_funding_event_negative_rate(self):
        event = self.FundingEvent.create(
            {
                "symbol": "ETHUSDT",
                "funding_rate": -0.005,
                "funding_direction": "received",
            }
        )
        self.assertEqual(event.funding_rate, -0.005)
        self.assertEqual(event.funding_direction, "received")

    def test_create_funding_event_neutral(self):
        event = self.FundingEvent.create(
            {
                "symbol": "BTCUSDT",
                "funding_rate": 0.0,
                "funding_direction": "neutral",
            }
        )
        self.assertEqual(event.funding_direction, "neutral")

    def test_funding_event_has_event_datetime(self):
        event = self.FundingEvent.create(
            {
                "symbol": "BTCUSDT",
                "funding_rate": 0.01,
            }
        )
        self.assertTrue(event.event_datetime)

    def test_funding_event_display_name(self):
        event = self.FundingEvent.create(
            {
                "symbol": "BTCUSDT",
                "funding_rate": 0.010000,
                "funding_direction": "paid",
            }
        )
        self.assertIn("BTCUSDT", event.display_name)
        self.assertIn("Paid", event.display_name)
        self.assertIn("0.010000", event.display_name)
