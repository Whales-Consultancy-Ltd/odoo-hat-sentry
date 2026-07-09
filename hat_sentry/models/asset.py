from odoo import _, api, fields, models


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
        domain=(
            "[('name', 'in', ('BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'ADA', 'XRP',"
            " 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM', 'LTC', 'BCH'))]"
        ),
        help="Linked pseudo-currency for this asset",
    )
    active = fields.Boolean(string="Active", default=True)
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

    @api.constrains("bucket")
    def _check_bucket_consistency(self):
        for record in self:
            if record.bucket not in dict(self._fields["bucket"].selection):
                raise models.ValidationError(_("Invalid bucket: %s") % record.bucket)
