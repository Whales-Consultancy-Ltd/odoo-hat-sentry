from odoo import api, fields, models


class HatSentryEarnPosition(models.Model):
    _name = "hat_sentry.earn.position"
    _description = "Earn Position"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "snapshot_id desc"

    snapshot_id = fields.Many2one(
        "hat_sentry.portfolio.snapshot", string="Snapshot", required=True, ondelete="cascade", index=True
    )
    asset_id = fields.Many2one("hat_sentry.asset", string="Asset", required=True, index=True)
    product_type = fields.Selection(
        [
            ("flexible", "Flexible"),
            ("locked", "Locked"),
        ],
        string="Product Type",
        required=True,
    )
    amount = fields.Float(string="Amount", digits=(16, 8), default=0.0)
    value_usdt = fields.Monetary(string="Value (USDT)", currency_field="currency_id")
    apy = fields.Float(string="APY %", digits=(16, 4))
    locked_until = fields.Date(string="Locked Until")
    interest_24h = fields.Monetary(string="24h Interest", currency_field="currency_id")
    interest_30d = fields.Monetary(string="30d Interest", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", related="snapshot_id.currency_id", string="Currency", readonly=True, store=False
    )
    company_id = fields.Many2one(
        "res.company", related="snapshot_id.company_id", string="Company", readonly=True, store=True
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")

    @api.depends("asset_id", "product_type")
    def _compute_display_name(self):
        for record in self:
            asset = record.asset_id.symbol if record.asset_id else "?"
            product = dict(record._fields["product_type"].selection).get(record.product_type, "?")
            record.display_name = f"{asset} ({product})"
