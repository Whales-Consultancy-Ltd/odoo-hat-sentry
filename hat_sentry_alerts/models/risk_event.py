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
            ("ignored", "Ignored"),
        ],
        string="State",
        default="new",
        tracking=True,
    )
    acknowledged_by = fields.Many2one("res.users", string="Acknowledged by", readonly=True)
    acknowledged_at = fields.Datetime(string="Acknowledged at", readonly=True)
    resolved_by = fields.Many2one("res.users", string="Resolved by", readonly=True)
    resolved_at = fields.Datetime(string="Resolved at", readonly=True)
    current_value = fields.Float(string="Current Value")
    max_observed_value = fields.Float(string="Max Observed Value")
    occurrence_count = fields.Integer(string="Occurrences", default=1)
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

    def action_acknowledge(self):
        self.write({
            "acknowledged_by": self.env.uid,
            "acknowledged_at": fields.Datetime.now(),
            "state": "acknowledged",
        })

    def action_resolve(self):
        self.write({
            "resolved_by": self.env.uid,
            "resolved_at": fields.Datetime.now(),
            "state": "resolved",
        })

    def action_ignore(self):
        self.write({"state": "ignored"})
