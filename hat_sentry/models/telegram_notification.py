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
        icon = severity_icons.get(alert.severity or "", "🔔")
        return (
            f"{icon} *Hat Sentry Alert*\n"
            f"*{alert.title or 'No title'}*\n\n"
            f"Severity: {(alert.severity or 'unknown').upper()}\n"
            f"Category: {alert.category or 'N/A'}\n\n"
            f"_{alert.recommended_action or 'No action recommended'}_"
        )

    def _send_message(self, bot_token, chat_id, message):
        """Send a message to Telegram via Bot API with retry."""
        import time
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        max_retries = 3
        for attempt in range(max_retries):
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
                if response.status_code == 200:
                    _logger.info("Telegram notification sent: %s", message[:50])
                    return True
                elif response.status_code == 429:
                    retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                    _logger.warning("Telegram rate limited, retrying after %ss", retry_after)
                    time.sleep(retry_after)
                    continue
                else:
                    _logger.warning("Telegram API error %s: %s", response.status_code, response.text)
                    return False
            except requests.exceptions.RequestException as e:
                _logger.warning("Telegram attempt %d/%d failed: %s", attempt + 1, max_retries, str(e))
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        _logger.error("Telegram message failed after %d attempts", max_retries)
        return False
