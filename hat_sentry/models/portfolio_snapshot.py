import json

from odoo import api, fields, models


class HatSentryPortfolioSnapshot(models.Model):
    _name = "hat_sentry.portfolio.snapshot"
    _description = "Portfolio Snapshot"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "snapshot_datetime"
    _order = "snapshot_datetime desc"

    snapshot_datetime = fields.Datetime(
        string="Snapshot Date", default=fields.Datetime.now, required=True, index=True, tracking=True
    )
    total_value = fields.Monetary(string="Total Value", currency_field="currency_id", tracking=True)
    spot_value = fields.Monetary(string="Spot Value", currency_field="currency_id")
    futures_margin_value = fields.Monetary(string="Futures Margin", currency_field="currency_id")
    futures_notional_value = fields.Monetary(string="Futures Notional", currency_field="currency_id")
    stablecoin_value = fields.Monetary(string="Stablecoin Reserve", currency_field="currency_id")
    core_value = fields.Monetary(string="Core Holdings", currency_field="currency_id")
    passive_income_value = fields.Monetary(string="Passive Income Value", currency_field="currency_id")
    experimental_value = fields.Monetary(string="Experimental Value", currency_field="currency_id")
    health_score = fields.Integer(
        string="Health Score",
        default=50,
        help="Composite health score 0-100",
        tracking=True,
        compute="_compute_health_score",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.ref("base.USD", raise_if_not_found=False).id
        if self.env.ref("base.USD", raise_if_not_found=False)
        else False,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, index=True
    )

    sync_status = fields.Selection(
        [
            ("complete", "Complete"),
            ("partial", "Partial"),
            ("failed", "Failed"),
        ],
        string="Sync Status",
        default="complete",
        readonly=True,
        tracking=True,
    )
    data_age_minutes = fields.Integer(
        string="Data Age (minutes)",
        compute="_compute_data_age",
        store=True,
    )

    balance_ids = fields.One2many("hat_sentry.balance", "snapshot_id", string="Balances")
    futures_position_ids = fields.One2many("hat_sentry.futures.position", "snapshot_id", string="Futures Positions")
    earn_position_ids = fields.One2many("hat_sentry.earn.position", "snapshot_id", string="Earn Positions")

    @api.depends("total_value", "futures_notional_value", "stablecoin_value", "core_value", "passive_income_value")
    def _compute_health_score(self):
        for record in self:
            score = 50
            if record.total_value and record.total_value > 0:
                if record.futures_notional_value:
                    exposure_pct = record.futures_notional_value / record.total_value * 100
                    if exposure_pct <= 5:
                        score += 15
                    elif exposure_pct <= 10:
                        score += 5
                    else:
                        score -= 15
                if record.stablecoin_value:
                    stable_pct = record.stablecoin_value / record.total_value * 100
                    if stable_pct >= 10:
                        score += 15
                    elif stable_pct >= 5:
                        score += 5
                    else:
                        score -= 5
                if record.core_value:
                    core_pct = record.core_value / record.total_value * 100
                    if core_pct >= 30:
                        score += 10
                if record.passive_income_value and record.passive_income_value > 0:
                    score += 10
            record.health_score = max(0, min(100, score))

    @api.depends("snapshot_datetime")
    def _compute_data_age(self):
        now = fields.Datetime.now()
        for record in self:
            if record.snapshot_datetime:
                delta = now - record.snapshot_datetime
                record.data_age_minutes = int(delta.total_seconds() / 60)
            else:
                record.data_age_minutes = 0

    # ---------------------------------------------------------------------------
    # P&L Fields
    # ---------------------------------------------------------------------------
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

    pnl_since_last = fields.Monetary(
        string="P&L Since Last Snapshot",
        currency_field="currency_id",
        compute="_compute_pnl_since_last",
        store=True,
        readonly=True,
        help="Change in total value since previous snapshot",
    )

    pnl_pct_since_last = fields.Float(
        string="P&L % Since Last Snapshot",
        digits=(16, 2),
        compute="_compute_pnl_since_last",
        store=True,
        readonly=True,
        help="Percentage change since previous snapshot",
    )

    previous_snapshot_id = fields.Many2one(
        "hat_sentry.portfolio.snapshot",
        string="Previous Snapshot",
        compute="_compute_previous_snapshot",
        store=False,
        help="Previous snapshot for comparison (same company/currency)",
    )

    # Allocation fields
    allocation_json = fields.Text(
        string="Allocation Data (JSON)",
        compute="_compute_allocation_json",
        store=True,
        readonly=True,
        help="JSON dump of allocation percentages by bucket and asset",
    )

    total_exposure = fields.Monetary(
        string="Total Exposure",
        currency_field="currency_id",
        compute="_compute_exposure",
        store=True,
        readonly=True,
        help="Total notional exposure including futures",
    )

    allocation_core_pct = fields.Float(
        string="Core Allocation %",
        digits=(16, 2),
        compute="_compute_allocation_pcts",
        store=True,
    )

    allocation_stable_pct = fields.Float(
        string="Stable Reserve %",
        digits=(16, 2),
        compute="_compute_allocation_pcts",
        store=True,
    )

    allocation_trading_pct = fields.Float(
        string="Trading Allocation %",
        digits=(16, 2),
        compute="_compute_allocation_pcts",
        store=True,
    )

    allocation_passive_pct = fields.Float(
        string="Passive Income %",
        digits=(16, 2),
        compute="_compute_allocation_pcts",
        store=True,
    )

    allocation_futures_pct = fields.Float(
        string="Futures Allocation %",
        digits=(16, 2),
        compute="_compute_allocation_pcts",
        store=True,
    )

    allocation_experimental_pct = fields.Float(
        string="Experimental Allocation %",
        digits=(16, 2),
        compute="_compute_allocation_pcts",
        store=True,
    )

    trading_value = fields.Monetary(
        string="Trading Value",
        currency_field="currency_id",
        compute="_compute_trading_value",
        store=True,
        help="Trading bucket value (spot - core - stablecoin)",
    )

    # ---------------------------------------------------------------------------
    # P&L Computed Methods
    # ---------------------------------------------------------------------------

    @api.depends("balance_ids.value_usdt", "futures_position_ids.unrealized_pnl")
    def _compute_pnl_fields(self):
        for record in self:
            trades = self.env["hat_sentry.trade"].search([("snapshot_id", "=", record.id)])
            realized = sum(trades.mapped("realized_pnl") or [0.0])
            unrealized = sum(record.futures_position_ids.mapped("unrealized_pnl") or [0.0])
            record.total_realized_pnl = realized
            record.total_unrealized_pnl = unrealized
            record.total_pnl = realized + unrealized

    @api.depends("snapshot_datetime", "total_value", "company_id", "currency_id", "previous_snapshot_id")
    def _compute_pnl_since_last(self):
        for record in self:
            if not record.snapshot_datetime:
                record.pnl_since_last = 0.0
                record.pnl_pct_since_last = 0.0
                continue
            previous = record.previous_snapshot_id
            if previous and previous.total_value and previous.total_value > 0:
                diff = (record.total_value or 0.0) - previous.total_value
                record.pnl_since_last = diff
                record.pnl_pct_since_last = (diff / previous.total_value) * 100
            else:
                record.pnl_since_last = 0.0
                record.pnl_pct_since_last = 0.0

    @api.depends("snapshot_datetime", "company_id")
    def _compute_previous_snapshot(self):
        for record in self:
            if not record.snapshot_datetime or not record.company_id:
                record.previous_snapshot_id = False
                continue
            prev = self.search(
                [
                    ("company_id", "=", record.company_id.id),
                    ("snapshot_datetime", "<", record.snapshot_datetime),
                    ("id", "!=", record.id),
                ],
                order="snapshot_datetime desc, id desc",
                limit=1,
            )
            record.previous_snapshot_id = prev.id if prev else False

    @api.depends(
        "core_value",
        "stablecoin_value",
        "trading_value",
        "passive_income_value",
        "futures_notional_value",
        "experimental_value",
        "total_value",
    )
    def _compute_allocation_pcts(self):
        for record in self:
            total = record.total_value or 0.0
            if total <= 0:
                record.allocation_core_pct = 0.0
                record.allocation_stable_pct = 0.0
                record.allocation_trading_pct = 0.0
                record.allocation_passive_pct = 0.0
                record.allocation_futures_pct = 0.0
                record.allocation_experimental_pct = 0.0
                continue
            record.allocation_core_pct = (record.core_value or 0.0) / total * 100
            record.allocation_stable_pct = (record.stablecoin_value or 0.0) / total * 100
            spot = record.spot_value or 0.0
            core = record.core_value or 0.0
            stable = record.stablecoin_value or 0.0
            record.allocation_trading_pct = max(0.0, (spot - core - stable)) / total * 100
            record.allocation_passive_pct = (record.passive_income_value or 0.0) / total * 100
            record.allocation_futures_pct = (record.futures_notional_value or 0.0) / total * 100
            record.allocation_experimental_pct = (record.experimental_value or 0.0) / total * 100

    @api.depends("total_value", "futures_notional_value")
    def _compute_exposure(self):
        for record in self:
            record.total_exposure = (record.total_value or 0.0) + (record.futures_notional_value or 0.0)

    @api.depends(
        "total_value",
        "core_value",
        "stablecoin_value",
        "passive_income_value",
        "futures_notional_value",
        "experimental_value",
        "spot_value",
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

    @api.depends("spot_value", "core_value", "stablecoin_value")
    def _compute_trading_value(self):
        for record in self:
            record.trading_value = max(
                0.0, (record.spot_value or 0.0) - (record.core_value or 0.0) - (record.stablecoin_value or 0.0)
            )

    @api.model
    def _pct(self, value, total):
        if total and total > 0:
            return round((value or 0.0) / total * 100, 2)
        return 0.0
