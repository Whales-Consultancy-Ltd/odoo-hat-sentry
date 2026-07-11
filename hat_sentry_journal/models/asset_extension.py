from odoo import api, fields, models


class HatSentryAsset(models.Model):
    _inherit = "hat_sentry.asset"

    trade_count = fields.Integer(
        string="Trade Count",
        compute="_compute_trade_stats",
    )
    total_trade_pnl = fields.Monetary(
        string="Total Trade P&L",
        currency_field="currency_id",
        compute="_compute_trade_stats",
    )

    @api.depends()
    def _compute_trade_stats(self):
        for record in self:
            trades = self.env["hat_sentry.trade"].search([("asset_id", "=", record.id)])
            record.trade_count = len(trades)
            record.total_trade_pnl = sum(trades.mapped("realized_pnl"))
