import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HatSentryAsset(models.Model):
    _name = "hat_sentry.asset"
    _description = "Crypto Asset"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "symbol"
    _order = "watchlist_status, conviction desc, symbol"

    _unique_symbol_company = models.Constraint(
        "unique(symbol, company_id)",
        "Asset already exists for this company!",
    )
    _positive_values = models.Constraint(
        "CHECK(value_usdt >= 0)",
        "Value must be non-negative!",
    )

    symbol = fields.Char(string="Symbol", required=True, index=True, tracking=True)
    name = fields.Char(string="Name", tracking=True)
    asset_type = fields.Selection(
        [
            ("crypto", "Crypto"),
            ("stablecoin", "Stablecoin"),
            ("fiat", "Fiat"),
        ],
        string="Asset Type",
        required=True,
        default="crypto",
        tracking=True,
    )
    bucket = fields.Selection(
        [
            ("core", "Core"),
            ("stable_reserve", "Stable Reserve"),
            ("passive_income", "Passive Income"),
            ("trading", "Trading"),
            ("futures", "Futures"),
            ("experimental", "Experimental"),
        ],
        string="Bucket",
        required=True,
        default="core",
        tracking=True,
    )
    is_stablecoin = fields.Boolean(string="Is Stablecoin", compute="_compute_is_stablecoin", store=True)
    is_core_asset = fields.Boolean(string="Is Core Asset", compute="_compute_is_core_asset", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Reference Currency",
        default=lambda self: self.env.ref("base.USD", raise_if_not_found=False).id
        if self.env.ref("base.USD", raise_if_not_found=False)
        else False,
        help="All crypto values denominated in USD",
    )
    active = fields.Boolean(string="Active", default=True)
    color = fields.Integer(string="Color Index")
    open_position_count = fields.Integer(
        string="Open Positions",
        compute="_compute_open_position_count",
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True,
        check_company=True,
    )

    # Watchlist fields
    watchlist_group_id = fields.Many2one(
        "hat_sentry.watchlist.group",
        string="Watchlist Group",
        index=True,
        tracking=True,
        check_company=True,
    )
    thesis = fields.Text(string="Investment Thesis", help="Why this asset is in your portfolio")
    invalidation_level = fields.Text(string="Invalidation Level", help="Conditions that would trigger an exit")
    review_date = fields.Date(string="Next Review Date", tracking=True, index=True)
    last_reviewed_at = fields.Datetime(string="Last Reviewed")
    conviction = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Conviction",
        default="medium",
        tracking=True,
    )
    watchlist_status = fields.Selection(
        [
            ("active", "Active"),
            ("watching", "Watching"),
            ("paused", "Paused"),
            ("archived", "Archived"),
        ],
        string="Watchlist Status",
        default="active",
        index=True,
        tracking=True,
    )
    max_allocation_pct = fields.Float(
        string="Max Allocation %", digits=(16, 2), help="Maximum % of portfolio for this asset"
    )
    entry_price_target = fields.Monetary(string="Target Entry Price", currency_field="currency_id")
    exit_price_target = fields.Monetary(string="Target Exit Price", currency_field="currency_id")
    notes = fields.Text(string="Notes")
    review_overdue = fields.Boolean(
        string="Review Overdue",
        compute="_compute_review_overdue",
        store=True,
        help="True when review_date is past due",
    )

    @api.depends("asset_type")
    def _compute_is_stablecoin(self):
        for record in self:
            record.is_stablecoin = record.asset_type == "stablecoin"

    @api.depends("bucket")
    def _compute_is_core_asset(self):
        for record in self:
            record.is_core_asset = record.bucket == "core"

    @api.depends()
    def _compute_open_position_count(self):
        for record in self:
            record.open_position_count = self.env["hat_sentry.futures.position"].search_count(
                [
                    ("symbol", "=", record.symbol),
                    ("state", "=", "open"),
                ]
            )

    @api.constrains("bucket")
    def _check_bucket_consistency(self):
        for record in self:
            if record.bucket not in dict(self._fields["bucket"].selection):
                raise ValidationError(_("Invalid bucket: %s") % record.bucket)

    @api.depends("review_date")
    def _compute_review_overdue(self):
        today = fields.Date.today()
        for record in self:
            record.review_overdue = bool(record.review_date and record.review_date < today)

    def action_mark_reviewed(self):
        """Mark this asset as reviewed today."""
        self.write(
            {
                "last_reviewed_at": fields.Datetime.now(),
                "review_date": False,
            }
        )

    @api.model
    def _cron_check_reviews(self):
        """Check for overdue reviews and create alerts."""
        today = fields.Date.today()
        overdue = self.search(
            [
                ("review_date", "<", today),
                ("review_date", "!=", False),
                ("watchlist_status", "in", ["active", "watching"]),
            ]
        )
        for asset in overdue:
            self.env["hat_sentry.alert"].create(
                {
                    "severity": "warning",
                    "category": "portfolio",
                    "title": _("Review Overdue: %s") % asset.symbol,
                    "message": _("Review date was %s. Please update your thesis and invalidation levels.")
                    % asset.review_date,
                    "recommended_action": _("Review the asset and set a new review date"),
                    "company_id": asset.company_id.id,
                }
            )
        return len(overdue)
