from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hat_sentry_telegram_bot_token = fields.Char(
        string="Telegram Bot Token",
        config_parameter="hat_sentry.telegram_bot_token",
        help="Bot token from @BotFather on Telegram",
    )
    hat_sentry_telegram_chat_id = fields.Char(
        string="Telegram Chat ID",
        config_parameter="hat_sentry.telegram_chat_id",
        help="Chat ID where notifications will be sent",
    )
    hat_sentry_snapshot_interval = fields.Integer(
        string="Snapshot Interval (minutes)",
        default=5,
        config_parameter="hat_sentry.snapshot_interval",
    )
    hat_sentry_risk_check_interval = fields.Integer(
        string="Risk Check Interval (minutes)",
        default=5,
        config_parameter="hat_sentry.risk_check_interval",
    )
