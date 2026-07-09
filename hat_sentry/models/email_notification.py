import logging

from markupsafe import escape

from odoo import models

_logger = logging.getLogger(__name__)


class HatSentryEmailNotification(models.AbstractModel):
    _name = "hat_sentry.email.notification"
    _description = "Email Notification"

    def send_alert_email(self, alert_id):
        """Send an email notification for an emergency alert."""
        alert = self.env["hat_sentry.alert"].browse(alert_id)
        if not alert.exists():
            return False

        # Find the user to notify (Manager)
        manager_group = self.env.ref("hat_sentry.group_hat_sentry_manager")
        users = manager_group.users if manager_group else []

        for user in users:
            if user.email:
                self._send_email(user, alert)
        return True

    def _send_email(self, user, alert):
        """Send an email to a user about an alert."""
        mail_values = {
            "subject": f"[Hat Sentry] {alert.severity.upper()}: {alert.title}",
            "body_html": f"""
                <div style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #cc0000;">🚨 Hat Sentry Alert</h2>
                    <p><strong>{escape(alert.title)}</strong></p>
                    <table>
                        <tr><td>Severity:</td><td>{escape(alert.severity)}</td></tr>
                        <tr><td>Category:</td><td>{escape(alert.category)}</td></tr>
                    </table>
                    <p><em>{escape(alert.recommended_action)}</em></p>
                </div>
            """,
            "email_to": user.email,
            "email_from": self.env.company.email or self.env.user.email,
        }
        mail = self.env["mail.mail"].sudo().create(mail_values)
        mail.send()
