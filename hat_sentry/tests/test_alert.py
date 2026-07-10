from odoo.tests.common import TransactionCase


class TestAlert(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Alert = self.env["hat_sentry.alert"]

    def test_create_info_alert(self):
        alert = self.Alert.create(
            {
                "title": "Info Alert",
                "severity": "info",
                "message": "Everything is normal",
                "recommended_action": "No action needed",
            }
        )
        self.assertEqual(alert.severity, "info")
        self.assertEqual(alert.state, "new")

    def test_create_warning_alert(self):
        alert = self.Alert.create(
            {
                "title": "Warning Alert",
                "severity": "warning",
                "message": "Something to watch",
                "recommended_action": "Monitor the situation",
            }
        )
        self.assertEqual(alert.severity, "warning")

    def test_create_critical_alert(self):
        alert = self.Alert.create(
            {
                "title": "Critical Alert",
                "severity": "critical",
                "message": "Immediate attention needed",
                "recommended_action": "Take action now",
            }
        )
        self.assertEqual(alert.severity, "critical")

    def test_create_emergency_alert(self):
        alert = self.Alert.create(
            {
                "title": "Emergency Alert",
                "severity": "emergency",
                "message": "Liquidation risk",
                "recommended_action": "Close positions immediately",
            }
        )
        self.assertEqual(alert.severity, "emergency")

    def test_alert_default_category(self):
        alert = self.Alert.create(
            {
                "title": "Test Alert",
                "severity": "info",
                "message": "Test",
                "recommended_action": "Test action",
            }
        )
        self.assertEqual(alert.category, "portfolio")
        self.assertEqual(alert.state, "new")

    def test_alert_acknowledge(self):
        alert = self.Alert.create(
            {
                "title": "Ack Test",
                "severity": "warning",
                "message": "Please acknowledge",
                "recommended_action": "Acknowledge this",
            }
        )
        alert.state = "acknowledged"
        self.assertEqual(alert.state, "acknowledged")

    def test_alert_resolve(self):
        alert = self.Alert.create(
            {
                "title": "Resolve Test",
                "severity": "info",
                "message": "Resolve me",
                "recommended_action": "Resolve",
            }
        )
        alert.state = "resolved"
        self.assertEqual(alert.state, "resolved")
