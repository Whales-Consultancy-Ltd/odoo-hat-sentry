import logging
from datetime import datetime

from odoo import fields, models

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
            "snapshot_datetime": fields.Datetime.now(),
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
        spot_ok = False
        futures_ok = False

        # Batch fetch all prices
        all_prices = {}
        try:
            price_data = api.get_all_prices(credential)
            if isinstance(price_data, list):
                for item in price_data:
                    all_prices[item["symbol"]] = float(item["price"])
        except Exception as e:
            _logger.warning("Failed to batch-fetch prices: %s", e)

        # 1. Spot balances
        try:
            spot_data = api.get_spot_balances(credential)
            for bal in spot_data:
                symbol = bal["asset"]
                if symbol == "USDT":
                    price = 1.0
                else:
                    price = all_prices.get(f"{symbol}USDT", 0.0)
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
            spot_ok = True
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
            futures_ok = True
        except Exception as e:
            _logger.error("Futures collection failed: %s", str(e))
            self._create_alert(credential, f"Futures data collection failed: {e}", "warning")

        # 3. Determine sync status
        if not spot_ok and not futures_ok:
            _logger.error(
                "Both spot and futures collection failed for %s — skipping snapshot",
                credential.name,
            )
            return False

        if spot_ok and futures_ok:
            sync_status = "complete"
        else:
            sync_status = "partial"

        # 4. Create snapshot
        if balances:
            snapshot = self._create_snapshot_from_balances(credential, balances)
            snapshot.sync_status = sync_status
            if futures_positions:
                self._create_futures_positions(credential, futures_positions, snapshot)

        return True

    def collect_funding_events(self, credential):
        """Collect funding events from Binance income history."""
        api = self.env["hat_sentry_binance.api"]
        try:
            income_data = api.get_funding_income(credential, limit=100)

            snapshot = self.env["hat_sentry.portfolio.snapshot"].search(
                [
                    ("company_id", "=", credential.company_id.id),
                ],
                order="snapshot_datetime desc",
                limit=1,
            )

            for item in income_data:
                symbol = item.get("symbol", "")
                amount = float(item.get("income", 0))
                tran_id = str(item.get("tranId", ""))
                income_time_ts = int(item.get("time", 0))
                if income_time_ts <= 0:
                    continue
                income_time = datetime.fromtimestamp(income_time_ts / 1000)

                if tran_id:
                    existing = self.env["hat_sentry.funding.event"].search(
                        [("transaction_id", "=", tran_id)],
                        limit=1,
                    )
                    if existing:
                        continue

                position = False
                if snapshot:
                    position = self.env["hat_sentry.futures.position"].search(
                        [
                            ("snapshot_id", "=", snapshot.id),
                            ("symbol", "=", symbol),
                        ],
                        limit=1,
                    )

                funding_direction = "neutral"
                if amount > 0:
                    funding_direction = "received"
                elif amount < 0:
                    funding_direction = "paid"

                self.env["hat_sentry.funding.event"].create(
                    {
                        "position_id": position.id if position else False,
                        "symbol": symbol,
                        "funding_amount": amount,
                        "funding_direction": funding_direction,
                        "transaction_id": tran_id,
                        "event_datetime": income_time,
                    }
                )
        except Exception as e:
            _logger.error("Funding collection failed: %s", str(e))

    def sync_orders(self, credential, days_back=7):
        """Sync recent orders from Binance for all tracked symbols."""
        api = self.env["hat_sentry_binance.api"]

        assets = self.env["hat_sentry.asset"].search([("company_id", "=", credential.company_id.id)])
        symbols = [a.symbol + "USDT" if not a.symbol.endswith("USDT") else a.symbol for a in assets]

        positions = self.env["hat_sentry.futures.position"].search(
            [
                ("state", "=", "open"),
                ("company_id", "=", credential.company_id.id),
            ]
        )
        for pos in positions:
            sym = pos.symbol
            if sym not in symbols:
                symbols.append(sym)

        symbols = list(set(symbols))

        created_count = 0
        for symbol in symbols:
            try:
                try:
                    orders_data = api.get_all_orders(credential, symbol, limit=50)
                    for order_data in orders_data:
                        if self._create_or_update_order(credential, order_data, "spot"):
                            created_count += 1
                except Exception as e:
                    _logger.debug("No spot orders for %s: %s", symbol, str(e))

                try:
                    futures_orders = api.get_futures_all_orders(credential, symbol, limit=50)
                    for order_data in futures_orders:
                        if self._create_or_update_order(credential, order_data, "futures"):
                            created_count += 1
                except Exception as e:
                    _logger.debug("No futures orders for %s: %s", symbol, str(e))

            except Exception as e:
                _logger.error("Order sync failed for %s: %s", symbol, str(e))

        _logger.info(
            "Order sync complete: %d new/updated orders for %s",
            created_count,
            credential.name,
        )
        return created_count

    def _create_or_update_order(self, credential, order_data, market_type="spot"):
        """Create or update an order record from Binance API data."""
        order_id = str(order_data.get("orderId", order_data.get("orderId", "")))
        if not order_id:
            return False

        existing = self.env["hat_sentry.order"].search(
            [
                ("order_id_binance", "=", order_id),
                ("credential_id", "=", credential.id),
            ],
            limit=1,
        )

        if existing:
            existing.write(
                {
                    "status": order_data.get("status", existing.status).lower(),
                    "executed_qty": float(order_data.get("executedQty", existing.executed_qty)),
                    "cummulative_quote_qty": float(
                        order_data.get(
                            "cummulativeQuoteQty",
                            existing.cummulative_quote_qty or 0,
                        )
                    ),
                    "update_datetime": fields.Datetime.now(),
                }
            )
            return False

        status = order_data.get("status", "new").lower()
        order_time = order_data.get("time", 0) or order_data.get("transactTime", 0)
        order_datetime = fields.Datetime.fromtimestamp(order_time / 1000) if order_time > 0 else fields.Datetime.now()

        self.env["hat_sentry.order"].create(
            {
                "order_id_binance": order_id,
                "symbol": order_data.get("symbol", ""),
                "side": order_data.get("side", "buy").lower(),
                "order_type": self._map_binance_type(order_data.get("type", "market")),
                "price": float(order_data.get("price", 0)),
                "stop_price": float(order_data.get("stopPrice", 0)),
                "orig_qty": float(order_data.get("origQty", 0)),
                "executed_qty": float(order_data.get("executedQty", 0)),
                "cummulative_quote_qty": float(order_data.get("cummulativeQuoteQty", 0)),
                "status": status,
                "time_in_force": order_data.get("timeInForce", ""),
                "order_datetime": order_datetime,
                "update_datetime": fields.Datetime.now(),
                "credential_id": credential.id,
            }
        )
        return True

    def _map_binance_type(self, binance_type):
        """Map Binance order type to internal selection."""
        mapping = {
            "MARKET": "market",
            "LIMIT": "limit",
            "STOP_LOSS": "stop_loss",
            "STOP_LOSS_LIMIT": "stop_loss",
            "TAKE_PROFIT": "take_profit",
            "TAKE_PROFIT_LIMIT": "take_profit",
            "STOP_MARKET": "stop_market",
            "TAKE_PROFIT_MARKET": "take_profit",
        }
        return mapping.get(binance_type.upper(), "market")

    def cron_sync_orders(self):
        """Scheduled: sync orders for all companies."""
        companies = self.env["res.company"].search([])
        for company in companies:
            credential = (
                self.env["hat_sentry.credential"]
                .with_company(company)
                .search(
                    [("active", "=", True)],
                    limit=1,
                )
            )
            if credential:
                try:
                    self.with_company(company).sync_orders(credential)
                except Exception as e:
                    _logger.error(
                        "Order sync failed for company %s: %s",
                        company.name,
                        str(e),
                    )

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
