from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

BINANCE_STATUS_MAP = {
    "NEW": "new",
    "PARTIALLY_FILLED": "partially_filled",
    "FILLED": "filled",
    "CANCELED": "cancelled",
    "CANCELLED": "cancelled",
    "PENDING_CANCEL": "cancelled",
    "REJECTED": "rejected",
    "EXPIRED": "expired",
}


def _normalize_status(binance_status):
    """Map a Binance API status string to the internal Odoo selection value."""
    return BINANCE_STATUS_MAP.get(binance_status.upper(), "new")


class HatSentryOrder(models.Model):
    _name = "hat_sentry.order"
    _description = "Exchange Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "order_datetime desc"

    name = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        default=lambda self: _("New Order"),
    )
    order_id_binance = fields.Char(
        string="Binance Order ID",
        index=True,
        required=True,
    )
    symbol = fields.Char(string="Symbol", required=True, index=True)
    side = fields.Selection(
        [("buy", "Buy"), ("sell", "Sell")],
        string="Side",
        required=True,
    )
    order_type = fields.Selection(
        [
            ("market", "Market"),
            ("limit", "Limit"),
            ("stop_loss", "Stop Loss"),
            ("take_profit", "Take Profit"),
            ("stop_market", "Stop Market"),
        ],
        string="Order Type",
        required=True,
    )
    price = fields.Monetary(string="Price", currency_field="currency_id")
    stop_price = fields.Monetary(string="Stop Price", currency_field="currency_id")
    orig_qty = fields.Float(
        string="Original Quantity",
        digits=(16, 8),
        default=0.0,
    )
    executed_qty = fields.Float(
        string="Executed Quantity",
        digits=(16, 8),
        default=0.0,
    )
    cummulative_quote_qty = fields.Monetary(
        string="Cumulative Quote Qty",
        currency_field="currency_id",
    )
    status = fields.Selection(
        [
            ("new", "New"),
            ("partially_filled", "Partially Filled"),
            ("filled", "Filled"),
            ("cancelled", "Cancelled"),
            ("rejected", "Rejected"),
            ("expired", "Expired"),
        ],
        string="Status",
        default="new",
        tracking=True,
        index=True,
    )
    time_in_force = fields.Selection(
        [
            ("GTC", "Good Till Cancelled"),
            ("IOC", "Immediate or Cancel"),
            ("FOK", "Fill or Kill"),
        ],
        string="Time in Force",
    )
    order_datetime = fields.Datetime(
        string="Order Time",
        required=True,
        index=True,
    )
    update_datetime = fields.Datetime(string="Last Updated")
    trade_id = fields.Many2one(
        "hat_sentry.trade",
        string="Linked Trade",
        ondelete="set null",
    )
    credential_id = fields.Many2one(
        "hat_sentry.credential",
        string="Credential",
        required=True,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.ref("base.USD").id,
    )
    company_id = fields.Many2one(
        "res.company",
        related="credential_id.company_id",
        string="Company",
        readonly=True,
        store=True,
    )
    active = fields.Boolean(default=True)
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
    )

    @api.depends("order_id_binance", "symbol")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.symbol} #{record.order_id_binance}"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New Order")) == _("New Order"):
                vals["name"] = self.env["ir.sequence"].next_by_code("hat_sentry.order") or _("New Order")
        return super().create(vals_list)

    @api.constrains("order_id_binance", "credential_id")
    def _check_order_id_binance_unique(self):
        for record in self:
            domain = [
                ("order_id_binance", "=", record.order_id_binance),
                ("credential_id", "=", record.credential_id.id),
                ("id", "!=", record.id),
            ]
            if self.search_count(domain, limit=1):
                raise ValidationError(_("Order ID must be unique per credential!"))
