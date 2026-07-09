from odoo import api, fields, models


class HatSentryFuturesPosition(models.Model):
    _name = "hat_sentry.futures.position"
    _description = "Futures Position"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"
    _order = "snapshot_id desc, symbol"

    snapshot_id = fields.Many2one(
        "hat_sentry.portfolio.snapshot", string="Snapshot", required=True, ondelete="cascade", index=True
    )
    symbol = fields.Char(string="Symbol", required=True, index=True, tracking=True)
    side = fields.Selection([("long", "Long"), ("short", "Short")], string="Side", required=True)
    entry_price = fields.Float(string="Entry Price", digits=(16, 8))
    mark_price = fields.Float(string="Mark Price", digits=(16, 8))
    position_size = fields.Float(string="Position Size", digits=(16, 8))
    notional_value = fields.Monetary(string="Notional Value", currency_field="currency_id")
    margin = fields.Monetary(string="Margin", currency_field="currency_id")
    leverage = fields.Float(string="Leverage", default=1.0)
    margin_mode = fields.Selection(
        [("isolated", "Isolated"), ("cross", "Cross")], string="Margin Mode", default="cross"
    )
    liquidation_price = fields.Float(string="Liquidation Price", digits=(16, 8))
    distance_to_liquidation_pct = fields.Float(
        string="Distance to Liquidation %", digits=(16, 2), compute="_compute_liq_distance", store=True
    )
    unrealized_pnl = fields.Monetary(string="Unrealized PnL", currency_field="currency_id", tracking=True)
    unrealized_pnl_pct = fields.Float(string="Unrealized PnL %", digits=(16, 2))
    stop_loss_price = fields.Float(string="Stop Loss Price", digits=(16, 8))
    has_stop_loss = fields.Boolean(string="Has Stop Loss", compute="_compute_has_stop", store=True)
    is_stop_above_entry = fields.Boolean(string="Stop Above Entry (Long only)")
    funding_rate_current = fields.Float(string="Current Funding Rate", digits=(16, 6))
    next_funding_time = fields.Datetime(string="Next Funding Time")
    state = fields.Selection(
        [
            ("open", "Open"),
            ("at_risk", "At Risk"),
            ("flagged", "Flagged"),
            ("closed", "Closed"),
        ],
        string="State",
        default="open",
        tracking=True,
    )
    currency_id = fields.Many2one(
        "res.currency", related="snapshot_id.currency_id", string="Currency", readonly=True, store=False
    )
    company_id = fields.Many2one(
        "res.company", related="snapshot_id.company_id", string="Company", readonly=True, store=False
    )
    display_name = fields.Char(string="Display Name", compute="_compute_display_name")

    @api.depends("mark_price", "liquidation_price", "entry_price")
    def _compute_liq_distance(self):
        for record in self:
            if record.liquidation_price and record.mark_price and record.liquidation_price > 0:
                if record.side == "long":
                    distance = ((record.mark_price - record.liquidation_price) / record.liquidation_price) * 100
                else:
                    distance = ((record.liquidation_price - record.mark_price) / record.mark_price) * 100
                record.distance_to_liquidation_pct = max(0, distance)
            else:
                record.distance_to_liquidation_pct = 0.0

    @api.depends("stop_loss_price")
    def _compute_has_stop(self):
        for record in self:
            record.has_stop_loss = bool(record.stop_loss_price and record.stop_loss_price > 0)

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.symbol} ({record.side})"
