import json

from odoo import api, fields, models


class HatSentryPortfolioSnapshot(models.Model):
    _inherit = "hat_sentry.portfolio.snapshot"

    total_realized_pnl = fields.Monetary(
        string="Total Realized P&L",
        currency_field="currency_id",
        compute="_compute_pnl_fields",
        store=True,
        readonly=True,
        help="Sum of realized P&L from all trades linked to this snapshot",
    )

    total_unrealized_pnl = fields.Monetary(
        string="Total Unrealized P&L",
        currency_field="currency_id",
        compute="_compute_pnl_fields",
        store=True,
        readonly=True,
        help="Sum of unrealized P&L from futures positions",
    )

    total_pnl = fields.Monetary(
        string="Total P&L",
        currency_field="currency_id",
        compute="_compute_pnl_fields",
        store=True,
        readonly=True,
        help="Total realized + unrealized P&L",
    )

    @api.depends("balance_ids.value_usdt", "futures_position_ids.unrealized_pnl")
    def _compute_pnl_fields(self):
        for record in self:
            trades = self.env["hat_sentry.trade"].search([("snapshot_id", "=", record.id)])
            realized = sum(trades.mapped("realized_pnl") or [0.0])
            unrealized = sum(record.futures_position_ids.mapped("unrealized_pnl") or [0.0])
            record.total_realized_pnl = realized
            record.total_unrealized_pnl = unrealized
            record.total_pnl = realized + unrealized

    @api.depends(
        "total_value",
        "core_value",
        "stablecoin_value",
        "passive_income_value",
        "futures_notional_value",
        "experimental_value",
        "spot_value",
        "total_realized_pnl",
        "total_unrealized_pnl",
        "total_pnl",
    )
    def _compute_allocation_json(self):
        for record in self:
            total = record.total_value or 0.0
            data = {
                "total_value": total,
                "allocation": {
                    "core": {
                        "value": record.core_value or 0.0,
                        "pct": self._pct(record.core_value, total),
                    },
                    "stablecoin": {
                        "value": record.stablecoin_value or 0.0,
                        "pct": self._pct(record.stablecoin_value, total),
                    },
                    "passive_income": {
                        "value": record.passive_income_value or 0.0,
                        "pct": self._pct(record.passive_income_value, total),
                    },
                    "futures": {
                        "value": record.futures_notional_value or 0.0,
                        "pct": self._pct(record.futures_notional_value, total),
                    },
                    "experimental": {
                        "value": record.experimental_value or 0.0,
                        "pct": self._pct(record.experimental_value, total),
                    },
                },
                "pnl": {
                    "realized": record.total_realized_pnl or 0.0,
                    "unrealized": record.total_unrealized_pnl or 0.0,
                    "total": record.total_pnl or 0.0,
                },
            }
            record.allocation_json = json.dumps(data, indent=2)
