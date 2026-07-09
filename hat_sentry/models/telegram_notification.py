import logging

import requests
from odoo import models

_logger = logging.getLogger(__name__)


class HatSentryTelegram(models.AbstractModel):
    _name = "hat_sentry.telegram"
    _description = "Telegram Notification"

    def _get_telegram_config(self):
        """Get Telegram bot token and chat ID from system parameters."""
        icp = self.env["ir.config_parameter"].sudo()
        return {
            "bot_token": icp.get_param("hat_sentry.telegram_bot_token", ""),
            "chat_id": icp.get_param("hat_sentry.telegram_chat_id", ""),
        }

    def send_alert(self, alert_id):
        """Send a Telegram notification for an alert."""
        config = self._get_telegram_config()
        if not config["bot_token"] or not config["chat_id"]:
            _logger.warning("Telegram not configured - bot_token or chat_id missing")
            return False

        alert = self.env["hat_sentry.alert"].browse(alert_id)
        if not alert.exists():
            return False

        message = self._format_alert_message(alert)
        return self._send_message(config["bot_token"], config["chat_id"], message)

    def _format_alert_message(self, alert):
        """Format an alert as a Telegram message."""
        severity_icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨",
            "emergency": "🆘",
        }
        icon = severity_icons.get(alert.severity, "🔔")
        return (
            f"{icon} *Hat Sentry Alert*\n"
            f"*{alert.title}*\n\n"
            f"Severity: {alert.severity.upper()}\n"
            f"Category: {alert.category}\n\n"
            f"_{alert.recommended_action}_"
        )

    def _send_message(self, bot_token, chat_id, message):
        """Send a message to Telegram via Bot API."""
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            response.raise_for_status()
            _logger.info("Telegram notification sent: %s", message[:50])
            return True
        except requests.exceptions.RequestException as e:
            _logger.error("Telegram API error: %s", str(e))
            return False
