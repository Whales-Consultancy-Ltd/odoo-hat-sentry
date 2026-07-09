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
    health_score = fields.Integer(string="Health Score", default=50, help="Composite health score 0-100", tracking=True)
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
