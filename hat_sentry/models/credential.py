from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HatSentryCredential(models.Model):
    _name = "hat_sentry.credential"
    _description = "Exchange Credential"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "exchange"

    exchange = fields.Selection([("binance", "Binance")], string="Exchange", required=True, default="binance")
    api_key = fields.Char(string="API Key", required=True)
    api_secret = fields.Char(string="API Secret", required=True, groups="hat_sentry.group_hat_sentry_manager")
    permissions = fields.Selection(
        [
            ("read_only", "Read Only"),
        ],
        string="Permissions",
        default="read_only",
        required=True,
    )
    ip_whitelist = fields.Char(string="IP Whitelist")
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")

    @api.depends("exchange", "api_key")
    def _compute_display_name(self):
        for record in self:
            key_display = (record.api_key[:8] + "...") if record.api_key and len(record.api_key) > 8 else (record.api_key or "???")
            record.display_name = f"{record.exchange} ({key_display})"

    @api.constrains("permissions")
    def _check_read_only(self):
        for record in self:
            if record.permissions != "read_only":
                raise ValidationError(
                    _(
                        "Only read-only API keys are allowed in Hat Sentry. "
                        "Trading/withdrawal permissions are not supported."
                    )
                )
