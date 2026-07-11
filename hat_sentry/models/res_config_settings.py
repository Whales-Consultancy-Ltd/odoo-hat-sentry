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
    hat_sentry_binance_api_key = fields.Char(
        string="Binance API Key",
        config_parameter="hat_sentry.binance_api_key",
    )
    hat_sentry_binance_api_secret = fields.Char(
        string="Binance API Secret",
        config_parameter="hat_sentry.binance_api_secret",
    )
