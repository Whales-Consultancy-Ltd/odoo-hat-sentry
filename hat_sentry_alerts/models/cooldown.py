from odoo import _, api, fields, models


class HatSentryCooldown(models.Model):
    _name = "hat_sentry.cooldown"
    _description = "Trading Cooldown"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "start_datetime desc"

    start_datetime = fields.Datetime(string="Start", default=fields.Datetime.now, required=True)
    end_datetime = fields.Datetime(string="End", required=True)
    reason = fields.Text(string="Reason", required=True)
    triggered_by_event_id = fields.Many2one("hat_sentry.risk.event", string="Triggered By", ondelete="set null")
    active = fields.Boolean(
        string="Active",
        default=True,
        compute="_compute_active",
        store=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")

    @api.depends("start_datetime", "end_datetime")
    def _compute_active(self):
        now = fields.Datetime.now()
        for record in self:
            record.active = record.start_datetime <= now <= (record.end_datetime or now)

    @api.depends("start_datetime", "end_datetime")
    def _compute_display_name(self):
        for record in self:
            end_str = record.end_datetime.date() if record.end_datetime else "?"
            record.display_name = f"Cooldown: {record.start_datetime.date()} \u2192 {end_str}"
