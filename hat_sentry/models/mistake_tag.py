from odoo import fields, models


class HatSentryMistakeTag(models.Model):
    _name = "hat_sentry.mistake.tag"
    _description = "Mistake Tag"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string="Color", default=0)
