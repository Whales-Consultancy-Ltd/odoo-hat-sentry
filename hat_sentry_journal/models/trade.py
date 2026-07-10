from odoo import _, api, fields, models


class HatSentryTrade(models.Model):
    _name = "hat_sentry.trade"
    _description = "Trade"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "entry_date desc, id desc"

    name = fields.Char(string="Reference", required=True, copy=False, default=lambda self: _("New Trade"))
    asset_id = fields.Many2one("hat_sentry.asset", string="Asset", required=True, index=True)
    exchange = fields.Selection(
        [("binance", "Binance"), ("manual", "Manual")],
        string="Exchange",
        default="manual",
        required=True,
    )
    direction = fields.Selection(
        [("buy", "Buy"), ("sell", "Sell")],
        string="Direction",
        required=True,
    )
    order_type = fields.Selection(
        [
            ("market", "Market"),
            ("limit", "Limit"),
            ("stop_loss", "Stop Loss"),
            ("take_profit", "Take Profit"),
        ],
        string="Order Type",
        default="market",
    )
    quantity = fields.Float(string="Quantity", digits=(16, 8), required=True)
    entry_price = fields.Monetary(string="Entry Price", currency_field="currency_id")
    exit_price = fields.Monetary(string="Exit Price", currency_field="currency_id")
    total_fees = fields.Monetary(string="Total Fees", currency_field="currency_id", default=0.0)
    realized_pnl = fields.Monetary(
        string="Realized P&L",
        currency_field="currency_id",
        compute="_compute_pnl",
        store=True,
        readonly=True,
    )
    realized_pnl_pct = fields.Float(
        string="Realized P&L %",
        digits=(16, 2),
        compute="_compute_pnl",
        store=True,
        readonly=True,
    )
    state = fields.Selection(
        [("open", "Open"), ("closed", "Closed"), ("cancelled", "Cancelled")],
        string="State",
        default="open",
        tracking=True,
    )
    entry_date = fields.Datetime(string="Entry Date", default=fields.Datetime.now, required=True)
    exit_date = fields.Datetime(string="Exit Date")
    futures_position_id = fields.Many2one(
        "hat_sentry.futures.position",
        string="Futures Position",
        ondelete="set null",
    )
    snapshot_id = fields.Many2one(
        "hat_sentry.portfolio.snapshot",
        string="Portfolio Snapshot",
        ondelete="set null",
    )
    decision_log_id = fields.Many2one(
        "hat_sentry.decision.log",
        string="Decision Log",
        ondelete="set null",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="asset_id.currency_id",
        string="Currency",
        readonly=True,
        store=False,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    active = fields.Boolean(default=True)

    @api.depends("entry_price", "exit_price", "quantity", "direction", "total_fees", "state")
    def _compute_pnl(self):
        for record in self:
            if record.state != "closed" or not record.exit_price or not record.entry_price:
                record.realized_pnl = 0.0
                record.realized_pnl_pct = 0.0
                continue
            if record.direction == "buy":
                pnl = (record.exit_price - record.entry_price) * record.quantity - record.total_fees
            else:
                pnl = (record.entry_price - record.exit_price) * record.quantity - record.total_fees
            record.realized_pnl = pnl
            cost_basis = record.entry_price * record.quantity
            record.realized_pnl_pct = (pnl / cost_basis * 100) if cost_basis else 0.0

    @api.model
    def create(self, vals):
        if vals.get("name", _("New Trade")) == _("New Trade"):
            vals["name"] = self.env["ir.sequence"].next_by_code("hat_sentry.trade") or _("New Trade")
        return super().create(vals)
