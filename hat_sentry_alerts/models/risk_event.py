from odoo import api, fields, models


class HatSentryRiskEvent(models.Model):
    _name = "hat_sentry.risk.event"
    _description = "Risk Breach Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "breach_datetime desc"

    risk_limit_id = fields.Many2one("hat_sentry.risk.limit", string="Risk Limit", required=True, index=True)
    limit_type = fields.Selection(
        string="Limit Type",
        related="risk_limit_id.limit_type",
        store=True,
        readonly=True,
    )
    actual_value = fields.Float(string="Actual Value", required=True, digits=(16, 4))
    threshold_value = fields.Float(string="Threshold", required=True, digits=(16, 4))
    breach_datetime = fields.Datetime(
        string="Breach Time",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("acknowledged", "Acknowledged"),
            ("resolved", "Resolved"),
        ],
        string="State",
        default="new",
        tracking=True,
    )
    alert_id = fields.Many2one("hat_sentry.alert", string="Related Alert", ondelete="set null")
    snapshot_id = fields.Many2one(
        "hat_sentry.portfolio.snapshot",
        string="Snapshot",
        ondelete="set null",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")

    @api.depends("risk_limit_id", "limit_type", "breach_datetime")
    def _compute_display_name(self):
        for record in self:
            type_name = dict(record._fields["limit_type"].selection).get(record.limit_type, record.limit_type)
            record.display_name = f"{type_name} Breach @ {record.breach_datetime}"
