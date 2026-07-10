from odoo import fields, models


class HatSentryRiskLimit(models.Model):
    _name = "hat_sentry.risk.limit"
    _description = "Risk Limit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "limit_type, name"

    name = fields.Char(string="Name", required=True)
    limit_type = fields.Selection(
        [
            ("max_daily_loss", "Max Daily Loss"),
            ("max_position_size", "Max Position Size"),
            ("max_leverage", "Max Leverage"),
            ("max_allocation_pct", "Max Allocation %"),
            ("max_speculative_pct", "Max Speculative %"),
            ("max_trades_per_day", "Max Trades per Day"),
            ("min_stablecoin_pct", "Min Stablecoin Reserve %"),
            ("max_futures_exposure_pct", "Max Futures Exposure %"),
            ("max_concentration_pct", "Max Single Asset %"),
        ],
        string="Limit Type",
        required=True,
        index=True,
    )
    value = fields.Float(
        string="Limit Value",
        required=True,
        help="Threshold value for this limit",
    )
    comparison = fields.Selection(
        [
            ("gt", "Greater Than (>)"),
            ("gte", "Greater Than or Equal (>=)"),
            ("lt", "Less Than (<)"),
            ("lte", "Less Than or Equal (<=)"),
        ],
        string="Comparison",
        default="gt",
        required=True,
        help="How actual value is compared to limit. Breach = actual comparison value is True.",
    )
    severity_on_breach = fields.Selection(
        [
            ("warning", "Warning"),
            ("critical", "Critical"),
            ("emergency", "Emergency"),
        ],
        string="Severity on Breach",
        default="warning",
        required=True,
    )
    active = fields.Boolean(string="Active", default=True)
    description = fields.Text(string="Description")
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
