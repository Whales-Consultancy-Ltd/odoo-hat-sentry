import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class DigestDigest(models.Model):
    _inherit = "digest.digest"

    # ---- KPI booleans (enable/disable toggle) ----
    kpi_hat_portfolio_value = fields.Boolean(string="Portfolio Value")
    kpi_hat_portfolio_value_value = fields.Monetary(
        compute="_compute_kpi_hat_portfolio_value",
        currency_field="currency_id",
    )

    kpi_hat_futures_exposure = fields.Boolean(string="Futures Exposure")
    kpi_hat_futures_exposure_value = fields.Float(
        compute="_compute_kpi_hat_futures_exposure",
        digits=(16, 2),
    )

    kpi_hat_health_score = fields.Boolean(string="Health Score")
    kpi_hat_health_score_value = fields.Integer(
        compute="_compute_kpi_hat_health_score",
    )

    kpi_hat_alerts_open = fields.Boolean(string="Open Alerts")
    kpi_hat_alerts_open_value = fields.Integer(
        compute="_compute_kpi_hat_alerts_open",
    )

    kpi_hat_stablecoin_reserve = fields.Boolean(string="Stable Reserve")
    kpi_hat_stablecoin_reserve_value = fields.Float(
        compute="_compute_kpi_hat_stablecoin_reserve",
        digits=(16, 2),
    )

    # ---- Compute methods ----
    def _get_latest_snapshot(self, company):
        """Get the most recent portfolio snapshot for a company."""
        return (
            self.env["hat_sentry.portfolio.snapshot"]
            .sudo()
            .search(
                [
                    ("company_id", "=", company.id),
                ],
                order="snapshot_datetime desc",
                limit=1,
            )
        )

    def _compute_kpi_hat_portfolio_value(self):
        start, end, companies = self._get_kpi_compute_parameters()
        for digest in self:
            company = digest.company_id or self.env.company
            snapshot = digest.with_company(company)._get_latest_snapshot(company)
            digest.kpi_hat_portfolio_value_value = snapshot.total_value if snapshot else 0.0

    def _compute_kpi_hat_futures_exposure(self):
        start, end, companies = self._get_kpi_compute_parameters()
        for digest in self:
            company = digest.company_id or self.env.company
            snapshot = digest.with_company(company)._get_latest_snapshot(company)
            if snapshot and snapshot.total_value and snapshot.total_value > 0:
                exposure = snapshot.total_value and snapshot.futures_notional_value or 0.0
                digest.kpi_hat_futures_exposure_value = (exposure / snapshot.total_value) * 100
            else:
                digest.kpi_hat_futures_exposure_value = 0.0

    def _compute_kpi_hat_health_score(self):
        start, end, companies = self._get_kpi_compute_parameters()
        for digest in self:
            company = digest.company_id or self.env.company
            snapshot = digest.with_company(company)._get_latest_snapshot(company)
            digest.kpi_hat_health_score_value = snapshot.health_score if snapshot else 0

    def _compute_kpi_hat_alerts_open(self):
        start, end, companies = self._get_kpi_compute_parameters()
        for digest in self:
            company = digest.company_id or self.env.company
            alert_count = (
                self.env["hat_sentry.alert"]
                .sudo()
                .search_count(
                    [
                        ("company_id", "=", company.id),
                        ("state", "in", ("new", "sent", "acknowledged")),
                    ]
                )
            )
            digest.kpi_hat_alerts_open_value = alert_count

    def _compute_kpi_hat_stablecoin_reserve(self):
        start, end, companies = self._get_kpi_compute_parameters()
        for digest in self:
            company = digest.company_id or self.env.company
            snapshot = digest.with_company(company)._get_latest_snapshot(company)
            if snapshot and snapshot.total_value and snapshot.total_value > 0:
                reserve = snapshot.stablecoin_value or 0.0
                digest.kpi_hat_stablecoin_reserve_value = (reserve / snapshot.total_value) * 100
            else:
                digest.kpi_hat_stablecoin_reserve_value = 0.0

    def _compute_kpis_actions(self, company, user):
        """Add actions for digest KPI clicks."""
        actions = super()._compute_kpis_actions(company, user)
        actions["kpi_hat_portfolio_value"] = "hat_sentry.action_hat_sentry_portfolio_snapshot"
        actions["kpi_hat_futures_exposure"] = "hat_sentry.action_hat_sentry_futures_position"
        actions["kpi_hat_health_score"] = "hat_sentry.action_hat_sentry_portfolio_snapshot"
        actions["kpi_hat_alerts_open"] = "hat_sentry.action_hat_sentry_alert"
        actions["kpi_hat_stablecoin_reserve"] = "hat_sentry.action_hat_sentry_portfolio_snapshot"
        return actions
