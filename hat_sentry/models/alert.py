from odoo import fields, models


class HatSentryAlert(models.Model):
    _name = "hat_sentry.alert"
    _description = "Alert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "title"
    _order = "create_date desc"

    severity = fields.Selection(
        [
            ("info", "Info"),
            ("warning", "Warning"),
            ("critical", "Critical"),
            ("emergency", "Emergency"),
        ],
        string="Severity",
        required=True,
        default="info",
        tracking=True,
    )

    category = fields.Selection(
        [
            ("portfolio", "Portfolio"),
            ("futures", "Futures"),
            ("funding", "Funding"),
            ("passive_income", "Passive Income"),
        ],
        string="Category",
        default="portfolio",
    )

    related_position_id = fields.Many2one("hat_sentry.futures.position", string="Related Position", check_company=True)
    title = fields.Char(string="Title", required=True, tracking=True)
    message = fields.Text(string="Message")
    recommended_action = fields.Text(string="Recommended Action", required=True)

    state = fields.Selection(
        [
            ("new", "New"),
            ("sent", "Sent"),
            ("acknowledged", "Acknowledged"),
            ("resolved", "Resolved"),
            ("ignored", "Ignored"),
        ],
        string="State",
        default="new",
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True,
        check_company=True,
    )
