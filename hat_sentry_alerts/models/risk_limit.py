from odoo import _, fields, models


class HatSentryRiskLimit(models.Model):
    _name = "hat_sentry.risk.limit"
    _description = "Risk Limit"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "limit_type, name"

    name = fields.Char(string=_("Name"), required=True)
    limit_type = fields.Selection(
        [
            ("max_daily_loss", _("Max Daily Loss")),
            ("max_position_size", _("Max Position Size")),
            ("max_leverage", _("Max Leverage")),
            ("max_allocation_pct", _("Max Allocation %")),
            ("max_speculative_pct", _("Max Speculative %")),
            ("max_trades_per_day", _("Max Trades per Day")),
            ("min_stablecoin_pct", _("Min Stablecoin Reserve %")),
            ("max_futures_exposure_pct", _("Max Futures Exposure %")),
            ("max_concentration_pct", _("Max Single Asset %")),
        ],
        string=_("Limit Type"),
        required=True,
        index=True,
    )
    value = fields.Float(
        string=_("Limit Value"),
        required=True,
        help=_("Threshold value for this limit"),
    )
    comparison = fields.Selection(
        [
            ("gt", _("Greater Than (>)")),
            ("gte", _("Greater Than or Equal (>=)")),
            ("lt", _("Less Than (<)")),
            ("lte", _("Less Than or Equal (<=)")),
        ],
        string=_("Comparison"),
        default="gt",
        required=True,
        help=_("How actual value is compared to limit. Breach = actual comparison value is True."),
    )
    severity_on_breach = fields.Selection(
        [
            ("warning", _("Warning")),
            ("critical", _("Critical")),
            ("emergency", _("Emergency")),
        ],
        string=_("Severity on Breach"),
        default="warning",
        required=True,
    )
    active = fields.Boolean(string=_("Active"), default=True)
    description = fields.Text(string=_("Description"))
    company_id = fields.Many2one(
        "res.company",
        string=_("Company"),
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
