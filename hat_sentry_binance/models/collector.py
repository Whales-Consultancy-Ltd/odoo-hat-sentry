import logging
from datetime import datetime

from odoo import models

_logger = logging.getLogger(__name__)


class HatSentryCollector(models.AbstractModel):
    _name = "hat_sentry_binance.collector"
    _description = "Binance Data Collector"

    def _get_active_credentials(self):
        """Get all active credentials across companies."""
        return self.env["hat_sentry.credential"].search(
            [
                ("active", "=", True),
            ]
        )

    def _create_snapshot_from_balances(self, credential, balances_data):
        """Create a portfolio snapshot from Binance balances."""
        # Calculate total value
        total_value = sum(b.get("value_usdt", 0) for b in balances_data if "value_usdt" in b)

        snapshot_vals = {
            "snapshot_datetime": datetime.now(),
            "total_value": total_value,
            "spot_value": sum(b.get("value_usdt", 0) for b in balances_data if b.get("account_type") == "spot"),
            "company_id": credential.company_id.id,
        }

        snapshot = self.env["hat_sentry.portfolio.snapshot"].create(snapshot_vals)

        # Create balance records
        for bal_data in balances_data:
            # Find or create the asset before creating the required balance link.
            symbol = bal_data.get("asset_symbol", "")
            asset = self.env["hat_sentry.asset"].search(
                [
                    ("symbol", "=", symbol),
                    ("company_id", "=", credential.company_id.id),
                ],
                limit=1,
            )
            if not asset and symbol:
                asset = self.env["hat_sentry.asset"].create(
                    {
                        "symbol": symbol,
                        "name": symbol,
                        "asset_type": "stablecoin" if symbol in ("USDT", "USDC", "BUSD", "DAI") else "crypto",
                        "bucket": "stable_reserve" if symbol in ("USDT", "USDC", "BUSD", "DAI") else "core",
                        "currency_id": self.env["hat_sentry.asset"]._ensure_currency(symbol).id,
                        "company_id": credential.company_id.id,
                    }
                )

            if not asset:
                _logger.warning("Skipping balance without asset symbol: %s", bal_data)
                continue

            balance_vals = {
                "snapshot_id": snapshot.id,
                "exchange": "binance",
                "account_type": bal_data.get("account_type", "spot"),
                "asset_id": asset.id,
                "free_amount": bal_data.get("free", 0),
                "locked_amount": bal_data.get("locked", 0),
                "price_usdt": bal_data.get("price_usdt", 0),
                "value_usdt": bal_data.get("value_usdt", 0),
            }
            self.env["hat_sentry.balance"].create(balance_vals)

        return snapshot

    def _create_futures_positions(self, credential, positions_data, snapshot):
        """Create futures position records for a snapshot."""
        for pos_data in positions_data:
            pos_vals = {
                "snapshot_id": snapshot.id,
                "symbol": pos_data.get("symbol"),
                "side": pos_data.get("side", "long"),
                "entry_price": pos_data.get("entry_price", 0),
                "mark_price": pos_data.get("mark_price", 0),
                "position_size": pos_data.get("position_size", 0),
                "notional_value": pos_data.get("notional_value", 0),
                "margin": pos_data.get("margin", 0),
                "leverage": pos_data.get("leverage", 1),
                "margin_mode": pos_data.get("margin_mode", "cross"),
                "liquidation_price": pos_data.get("liquidation_price", 0),
                "unrealized_pnl": pos_data.get("unrealized_pnl", 0),
                "unrealized_pnl_pct": pos_data.get("unrealized_pnl_pct", 0),
                "state": "open",
            }
            self.env["hat_sentry.futures.position"].create(pos_vals)

    def collect_snapshot(self, credential):
        """Collect a complete portfolio snapshot for one credential."""
        api = self.env["hat_sentry_binance.api"]

        balances = []

        # 1. Spot balances
        try:
            spot_data = api.get_spot_balances(credential)
            for bal in spot_data:
                symbol = bal["asset"]
                price = 1.0 if symbol == "USDT" else api.get_price_ticker(credential, f"{symbol}USDT")
                balances.append(
                    {
                        "asset_symbol": symbol,
                        "account_type": "spot",
                        "free": bal["free"],
                        "locked": bal["locked"],
                        "price_usdt": price,
                        "value_usdt": (bal["free"] + bal["locked"]) * price,
                    }
                )
        except Exception as e:
            _logger.error("Spot collection failed: %s", str(e))
            self._create_alert(credential, f"Spot data collection failed: {e}", "critical")

        # 2. Futures positions
        futures_positions = []
        try:
            positions_data = api.get_futures_positions(credential)
            for pos in positions_data:
                futures_positions.append(pos)
                # Add futures margin to balances
                balances.append(
                    {
                        "asset_symbol": pos["symbol"],
                        "account_type": "futures",
                        "free": pos["margin"],
                        "locked": 0,
                        "price_usdt": pos["mark_price"],
                        "value_usdt": pos["margin"],
                    }
                )
        except Exception as e:
            _logger.error("Futures collection failed: %s", str(e))
            self._create_alert(credential, f"Futures data collection failed: {e}", "warning")

        # 3. Create snapshot
        if balances:
            snapshot = self._create_snapshot_from_balances(credential, balances)
            if futures_positions:
                self._create_futures_positions(credential, futures_positions, snapshot)

        return True

    def collect_funding_events(self, credential):
        """Collect recent funding events."""
        api = self.env["hat_sentry_binance.api"]
        try:
            rates_data = api.get_funding_rates(credential, limit=50)

            # Get the most recent snapshot to link positions
            snapshot = self.env["hat_sentry.portfolio.snapshot"].search(
                [
                    ("company_id", "=", credential.company_id.id),
                ],
                order="snapshot_datetime desc",
                limit=1,
            )

            for rate in rates_data:
                symbol = rate.get("symbol", "")
                funding_rate = float(rate.get("fundingRate", 0))
                funding_time = datetime.fromtimestamp(int(rate.get("fundingTime", 0)) / 1000)

                # Find related position if snapshot exists
                position = False
                if snapshot:
                    position = self.env["hat_sentry.futures.position"].search(
                        [
                            ("snapshot_id", "=", snapshot.id),
                            ("symbol", "=", symbol),
                        ],
                        limit=1,
                    )

                self.env["hat_sentry.funding.event"].create(
                    {
                        "position_id": position.id if position else False,
                        "symbol": symbol,
                        "funding_rate": funding_rate * 100,  # convert to percentage
                        "funding_direction": "paid" if funding_rate > 0 else "received",
                        "event_datetime": funding_time,
                    }
                )
        except Exception as e:
            _logger.error("Funding collection failed: %s", str(e))

    def _create_alert(self, credential, message, severity="warning"):
        """Create an alert for a collection issue."""
        self.env["hat_sentry.alert"].create(
            {
                "severity": severity,
                "category": "portfolio",
                "title": f"Binance Connector: {message[:50]}",
                "message": message,
                "recommended_action": "Check Binance API status and credentials",
                "company_id": credential.company_id.id,
            }
        )

    # ---- Cron methods ----

    def cron_collect_snapshot(self):
        """Scheduled: collect snapshots for all companies."""
        companies = self.env["res.company"].search([])
        for company in companies:
            credential = (
                self.env["hat_sentry.credential"]
                .with_company(company)
                .search(
                    [
                        ("active", "=", True),
                    ],
                    limit=1,
                )
            )
            if credential:
                try:
                    self.with_company(company).collect_snapshot(credential)
                    _logger.info("Snapshot collected for company %s", company.name)
                except Exception as e:
                    _logger.error("Snapshot collection failed for company %s: %s", company.name, str(e))
            else:
                _logger.info("No active credentials for company %s, skipping", company.name)

    def cron_collect_funding(self):
        """Scheduled: collect funding events for all companies."""
        companies = self.env["res.company"].search([])
        for company in companies:
            credential = (
                self.env["hat_sentry.credential"]
                .with_company(company)
                .search(
                    [
                        ("active", "=", True),
                    ],
                    limit=1,
                )
            )
            if credential:
                try:
                    self.with_company(company).collect_funding_events(credential)
                except Exception as e:
                    _logger.error("Funding collection failed for company %s: %s", company.name, str(e))
