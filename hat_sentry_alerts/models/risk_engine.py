import logging
from datetime import timedelta

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class HatSentryRiskEngine(models.AbstractModel):
    _name = "hat_sentry.risk.engine"
    _description = "Risk Limit Evaluation Engine"

    def evaluate_limits(self, snapshot):
        """Evaluate all active risk limits against a portfolio snapshot.

        Creates risk events and alerts for any breaches.

        Args:
            snapshot: hat_sentry.portfolio.snapshot record
        """
        company = snapshot.company_id
        active_limits = self.env["hat_sentry.risk.limit"].search(
            [("active", "=", True), ("company_id", "=", company.id)]
        )

        if not active_limits:
            return

        for limit in active_limits:
            actual = self._get_actual_value(limit.limit_type, snapshot)
            if actual is None:
                continue

            threshold = limit.value
            breached = self._check_breach(actual, threshold, limit.comparison)

            if breached:
                self._create_breach(limit, actual, threshold, snapshot)

    def _get_actual_value(self, limit_type, snapshot):
        """Extract the actual value from snapshot based on limit type."""
        mapping = {
            "max_daily_loss": self._get_daily_pnl(snapshot),
            "max_position_size": snapshot.futures_notional_value,
            "max_leverage": self._get_max_leverage(snapshot),
            "max_allocation_pct": None,
            "max_speculative_pct": (
                (snapshot.experimental_value or 0.0) / (snapshot.total_value or 1.0) * 100
                if snapshot.total_value
                else 0.0
            ),
            "max_trades_per_day": self._get_trades_today(snapshot),
            "min_stablecoin_pct": (
                (snapshot.stablecoin_value or 0.0) / (snapshot.total_value or 1.0) * 100
                if snapshot.total_value
                else 0.0
            ),
            "max_futures_exposure_pct": (
                (snapshot.futures_notional_value or 0.0) / (snapshot.total_value or 1.0) * 100
                if snapshot.total_value
                else 0.0
            ),
            "max_concentration_pct": None,
        }
        return mapping.get(limit_type)

    def _get_daily_pnl(self, snapshot):
        """Get today's P&L from trades."""
        today = fields.Date.today()
        trades = self.env["hat_sentry.trade"].search(
            [("entry_date", ">=", today), ("company_id", "=", snapshot.company_id.id)]
        )
        return sum(trades.mapped("realized_pnl") or [0.0])

    def _get_max_leverage(self, snapshot):
        """Get max leverage across all futures positions."""
        positions = snapshot.futures_position_ids
        if not positions:
            return 0.0
        return max(positions.mapped("leverage") or [0.0])

    def _get_trades_today(self, snapshot):
        """Count trades today."""
        today = fields.Date.today()
        return self.env["hat_sentry.trade"].search_count(
            [("entry_date", ">=", today), ("company_id", "=", snapshot.company_id.id)]
        )

    def _check_breach(self, actual, threshold, comparison):
        """Check if actual value breaches the threshold."""
        if comparison == "gt":
            return actual > threshold
        if comparison == "gte":
            return actual >= threshold
        if comparison == "lt":
            return actual < threshold
        if comparison == "lte":
            return actual <= threshold
        return False

    def _create_breach(self, limit, actual, threshold, snapshot):
        """Create a risk event and alert for a breach."""
        today = fields.Date.today()
        existing = self.env["hat_sentry.risk.event"].search(
            [
                ("risk_limit_id", "=", limit.id),
                ("state", "in", ["new", "acknowledged"]),
                ("breach_datetime", ">=", today),
            ],
            limit=1,
        )

        if existing:
            return existing

        alert = self.env["hat_sentry.alert"].create(
            {
                "severity": limit.severity_on_breach,
                "category": "portfolio",
                "title": _("Risk Limit Breach: %s") % limit.name,
                "message": _("Actual: %.2f, Threshold: %.2f") % (actual, threshold),
                "recommended_action": _("Review your %s settings")
                % dict(limit._fields["limit_type"].selection).get(limit.limit_type, limit.limit_type),
                "company_id": snapshot.company_id.id,
            }
        )

        event = self.env["hat_sentry.risk.event"].create(
            {
                "risk_limit_id": limit.id,
                "actual_value": actual,
                "threshold_value": threshold,
                "breach_datetime": fields.Datetime.now(),
                "state": "new",
                "alert_id": alert.id,
                "snapshot_id": snapshot.id,
                "company_id": snapshot.company_id.id,
            }
        )

        if limit.severity_on_breach == "emergency":
            self._create_cooldown(event, snapshot)

        return event

    def _create_cooldown(self, event, snapshot):
        """Create a cooldown period for emergency breaches."""
        now = fields.Datetime.now()
        end = now + timedelta(hours=24)

        self.env["hat_sentry.cooldown"].create(
            {
                "start_datetime": now,
                "end_datetime": end,
                "reason": _("Emergency breach: %s") % event.risk_limit_id.name,
                "triggered_by_event_id": event.id,
                "company_id": snapshot.company_id.id,
            }
        )

    def get_active_cooldown(self, company):
        """Get currently active cooldown for a company."""
        now = fields.Datetime.now()
        return self.env["hat_sentry.cooldown"].search(
            [
                ("start_datetime", "<=", now),
                ("end_datetime", ">=", now),
                ("company_id", "=", company.id),
                ("active", "=", True),
            ],
            limit=1,
        )

    def _cron_evaluate_all(self):
        """Evaluate risk limits for all companies with recent snapshots."""
        companies = self.env["res.company"].search([])
        for company in companies:
            snapshot = self.env["hat_sentry.portfolio.snapshot"].search(
                [("company_id", "=", company.id)],
                order="snapshot_datetime desc",
                limit=1,
            )
            if snapshot:
                self.with_company(company).evaluate_limits(snapshot)
