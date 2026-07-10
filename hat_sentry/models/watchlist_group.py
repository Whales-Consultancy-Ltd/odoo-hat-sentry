from odoo import _, fields, models


class HatSentryWatchlistGroup(models.Model):
    _name = "hat_sentry.watchlist.group"
    _description = "Watchlist Group"
    _rec_name = "name"
    _order = "sequence, name"

    name = fields.Char(string=_("Name"), required=True)
    color = fields.Integer(string=_("Color"), default=0)
    sequence = fields.Integer(string=_("Sequence"), default=10)
    active = fields.Boolean(string=_("Active"), default=True)
    company_id = fields.Many2one(
        "res.company", string=_("Company"), default=lambda self: self.env.company, required=True, index=True
    )
