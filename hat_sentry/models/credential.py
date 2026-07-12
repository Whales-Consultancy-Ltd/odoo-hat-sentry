from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HatSentryCredential(models.Model):
    _name = "hat_sentry.credential"
    _description = "Exchange Credential"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "exchange"

    exchange = fields.Selection([("binance", "Binance")], string="Exchange", required=True, default="binance")
    api_key = fields.Char(string="API Key", required=True, copy=False, groups="hat_sentry.group_hat_sentry_manager")
    api_secret = fields.Char(
        string="API Secret", required=True, copy=False, groups="hat_sentry.group_hat_sentry_manager"
    )
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
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True,
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")
    last_validation_at = fields.Datetime(string="Last Validation")
    last_validation_status = fields.Selection(
        [
            ("success", "Success"),
            ("failed", "Failed"),
            ("never", "Never Validated"),
        ],
        string="Validation Status",
        default="never",
    )
    last_validation_message = fields.Text(string="Validation Message")
    environment = fields.Selection(
        [
            ("production", "Production"),
            ("testnet", "Testnet"),
        ],
        string="Environment",
        default="production",
    )
    last_successful_sync_at = fields.Datetime(string="Last Successful Sync")

    @api.depends("exchange", "environment")
    def _compute_display_name(self):
        for record in self:
            exchange = dict(record._fields["exchange"].selection).get(record.exchange, record.exchange or "???")
            environment = dict(record._fields["environment"].selection).get(
                record.environment, record.environment or "???"
            )
            record.display_name = _("%(exchange)s (%(environment)s)", exchange=exchange, environment=environment)

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

    def action_test_connection(self):
        """Test the API connection and update validation fields."""
        self.ensure_one()
        try:
            api = self.env["hat_sentry_binance.api"]
            success, message = api.validate_credentials(self)
            self.write({
                "last_validation_at": fields.Datetime.now(),
                "last_validation_status": "success" if success else "failed",
                "last_validation_message": message,
            })
            if success:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Connection Successful"),
                        "message": message,
                        "type": "success",
                        "sticky": False,
                    },
                }
            else:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Connection Failed"),
                        "message": message,
                        "type": "danger",
                        "sticky": True,
                    },
                }
        except Exception as e:
            self.write({
                "last_validation_at": fields.Datetime.now(),
                "last_validation_status": "failed",
                "last_validation_message": str(e),
            })
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Connection Error"),
                    "message": str(e),
                    "type": "danger",
                    "sticky": True,
                },
            }
