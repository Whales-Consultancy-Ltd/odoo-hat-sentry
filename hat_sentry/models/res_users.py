from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    hat_sentry_notify_email = fields.Boolean(string="Email Notifications", default=True)
    hat_sentry_notify_critical_only = fields.Boolean(string="Critical Only", default=False)
