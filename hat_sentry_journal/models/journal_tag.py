from odoo import fields, models


class HatSentryJournalTag(models.Model):
    _name = "hat_sentry.journal.tag"
    _description = "Journal Tag"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string="Color", default=0)
    active = fields.Boolean(default=True)
