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
        help="Linked pseudo-currency for this asset",
    )
    active = fields.Boolean(string="Active", default=True)
    open_position_count = fields.Integer(
        string="Open Positions",
        compute="_compute_open_position_count",
    )
    trade_count = fields.Integer(
        string="Trade Count",
        compute="_compute_trade_stats",
    )
    total_trade_pnl = fields.Monetary(
        string="Total Trade P&L",
        currency_field="currency_id",
        compute="_compute_trade_stats",
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True
    )

    # Watchlist fields
    watchlist_group_id = fields.Many2one(
        "hat_sentry.watchlist.group",
        string="Watchlist Group",
        index=True,
        tracking=True,
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

    @api.depends()
    def _compute_trade_stats(self):
        for record in self:
            try:
                trades = self.env["hat_sentry.trade"].search([("asset_id", "=", record.id)])
                record.trade_count = len(trades)
                record.total_trade_pnl = sum(trades.mapped("realized_pnl"))
            except KeyError:
                record.trade_count = 0
                record.total_trade_pnl = 0.0

    @api.constrains("bucket")
    def _check_bucket_consistency(self):
        for record in self:
            if record.bucket not in dict(self._fields["bucket"].selection):
                raise ValidationError(_("Invalid bucket: %s") % record.bucket)

    @api.model
    def _ensure_currency(self, symbol):
        """Ensure a res.currency exists for the given symbol. Auto-create if missing.

        Note: res.currency.name has size=3 (ISO 4217). Symbols longer than 3 chars
        are truncated. USDT/USDC are mapped to USD (stablecoins at 1:1 peg).
        """
        # Stablecoins map to USD
        if symbol in ("USDT", "USDC"):
            return self.env.ref("base.USD", raise_if_not_found=False) or self.env["res.currency"].search(
                [("name", "=", "USD")], limit=1
            )

        currency = self.env["res.currency"].search([("name", "=", symbol)], limit=1)
        if not currency:
            name = symbol[:3] if len(symbol) > 3 else symbol
            currency = self.env["res.currency"].create(
                {
                    "name": name,
                    "symbol": symbol,
                    "rounding": 0.01,
                    "active": True,
                    "position": "after",
                }
            )
            _logger.info("Auto-created res.currency for %s (name=%s)", symbol, name)
        return currency

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
