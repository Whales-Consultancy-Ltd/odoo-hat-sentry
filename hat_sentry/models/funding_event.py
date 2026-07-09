from odoo import api, fields, models


class HatSentryFundingEvent(models.Model):
    _name = "hat_sentry.funding.event"
    _description = "Funding Rate Event"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "event_datetime desc"

    position_id = fields.Many2one("hat_sentry.futures.position", string="Position", ondelete="cascade", index=True)
    symbol = fields.Char(string="Symbol", index=True)
    funding_rate = fields.Float(string="Funding Rate", digits=(16, 6))
    funding_amount = fields.Monetary(string="Funding Amount", currency_field="currency_id")
    funding_direction = fields.Selection(
        [
            ("paid", "Paid"),
            ("received", "Received"),
            ("neutral", "Neutral"),
        ],
        string="Direction",
    )
    event_datetime = fields.Datetime(string="Event Time", default=fields.Datetime.now, index=True)
    currency_id = fields.Many2one(
        "res.currency", related="position_id.snapshot_id.currency_id", string="Currency", readonly=True, store=False
    )
    company_id = fields.Many2one(
        "res.company", related="position_id.snapshot_id.company_id", string="Company", readonly=True, store=True
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")

    @api.depends("symbol", "funding_direction", "funding_rate")
    def _compute_display_name(self):
        for record in self:
            sym = record.symbol or "?"
            direction = dict(record._fields["funding_direction"].selection).get(record.funding_direction, "?")
            record.display_name = f"{sym} {direction} ({record.funding_rate:.6f}%)"
