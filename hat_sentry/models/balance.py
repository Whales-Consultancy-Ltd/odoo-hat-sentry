from odoo import api, fields, models


class HatSentryBalance(models.Model):
    _name = "hat_sentry.balance"
    _description = "Asset Balance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "value_usdt desc"

    _sql_constraints = [
        ("unique_balance", "unique(snapshot_id, asset_id, account_type)", "Balance already exists for this snapshot and asset!"),
    ]

    snapshot_id = fields.Many2one(
        "hat_sentry.portfolio.snapshot", string="Snapshot", required=True, ondelete="cascade", index=True,
        check_company=True,
    )
    exchange = fields.Selection([("binance", "Binance")], string="Exchange", default="binance", required=True)
    account_type = fields.Selection(
        [
            ("spot", "Spot"),
            ("futures", "Futures"),
            ("earn", "Earn"),
        ],
        string="Account Type",
        required=True,
        default="spot",
    )
    asset_id = fields.Many2one("hat_sentry.asset", string="Asset", required=True, index=True, check_company=True)
    free_amount = fields.Float(string="Free Amount", digits=(16, 8), default=0.0)
    locked_amount = fields.Float(string="Locked Amount", digits=(16, 8), default=0.0)
    total_amount = fields.Float(string="Total Amount", digits=(16, 8), compute="_compute_total", store=True)
    price_usdt = fields.Float(string="Price (USDT)", digits=(16, 8), default=0.0)
    value_usdt = fields.Monetary(string="Value (USDT)", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", related="snapshot_id.currency_id", string="Currency", readonly=True, store=False
    )
    company_id = fields.Many2one(
        "res.company", related="snapshot_id.company_id", string="Company", readonly=True, store=True
    )

    display_name = fields.Char(string="Display Name", compute="_compute_display_name")

    @api.depends("free_amount", "locked_amount")
    def _compute_total(self):
        for record in self:
            record.total_amount = record.free_amount + record.locked_amount

    @api.depends("asset_id", "snapshot_id", "account_type")
    def _compute_display_name(self):
        for record in self:
            asset_name = record.asset_id.symbol if record.asset_id else "?"
            record.display_name = f"[{record.snapshot_id.id}] {asset_name} - {record.account_type}"
