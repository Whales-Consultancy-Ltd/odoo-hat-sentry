import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HatSentryAsset(models.Model):
    _name = "hat_sentry.asset"
    _description = "Crypto Asset"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "symbol"
    _order = "symbol"

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
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True
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
