from odoo import _, fields, models


class HatSentryWatchlistGroup(models.Model):
    _name = "hat_sentry.watchlist.group"
    _description = "Watchlist Group"
    _rec_name = "name"
    _order = "sequence, name"

    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string="Color", default=0)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True,
        check_company=True,
    )
