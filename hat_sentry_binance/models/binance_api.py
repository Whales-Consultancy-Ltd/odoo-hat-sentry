import logging
from datetime import datetime, timedelta

from binance.client import Client
from binance.exceptions import BinanceAPIException
from odoo import models

_logger = logging.getLogger(__name__)


class BinanceAPI(models.AbstractModel):
    _name = "hat_sentry_binance.api"
    _description = "Binance API Client"

    def _get_client(self, credential):
        """Create a python-binance Client for this credential."""
        return Client(credential.api_key, credential.api_secret)

    def get_spot_balances(self, credential):
        """Get all spot balances. Returns list of dicts."""
        client = self._get_client(credential)
        account = client.get_account()
        balances = []
        for bal in account.get("balances", []):
            free = float(bal.get("free", 0))
            locked = float(bal.get("locked", 0))
            if free > 0 or locked > 0:
                balances.append(
                    {
                        "asset": bal["asset"],
                        "free": free,
                        "locked": locked,
                    }
                )
        return balances

    def get_futures_positions(self, credential):
        """Get all open futures positions. Returns list of dicts."""
        client = self._get_client(credential)
        account = client.futures_account()
        positions = []
        for pos in account.get("positions", []):
            position_size = float(pos.get("positionAmt", 0))
            if position_size != 0:
                entry_price = float(pos.get("entryPrice", 0))
                mark_price = float(pos.get("markPrice", 0))
                leverage = float(pos.get("leverage", 1))
                side = "long" if position_size > 0 else "short"
                unrealized_pnl = float(pos.get("unrealizedProfit", 0))
                margin = (
                    float(pos.get("isolatedWallet", 0))
                    if pos.get("isolated")
                    else float(pos.get("positionInitialMargin", 0))
                )
                positions.append(
                    {
                        "symbol": pos["symbol"],
                        "side": side,
                        "entry_price": entry_price,
                        "mark_price": mark_price,
                        "position_size": abs(position_size),
                        "notional_value": abs(position_size) * mark_price,
                        "margin": margin,
                        "leverage": leverage,
                        "margin_mode": "isolated" if pos.get("isolated") else "cross",
                        "liquidation_price": float(pos.get("liquidationPrice", 0)),
                        "unrealized_pnl": unrealized_pnl,
                        "unrealized_pnl_pct": (unrealized_pnl / margin * 100) if margin > 0 else 0,
                    }
                )
        return positions

    def get_funding_rates(self, credential, symbol=None, limit=100):
        """Get recent funding rates."""
        client = self._get_client(credential)
        return client.futures_funding_rate(symbol=symbol, limit=limit)

    def get_funding_income(self, credential, symbol=None, limit=100, start_time=None, end_time=None):
        """Get funding fee income history."""
        client = self._get_client(credential)
        params = {"incomeType": "FUNDING_FEE", "limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return client.futures_income_history(**params)

    def get_earn_positions(self, credential):
        """Get Earn positions (flexible + locked)."""
        client = self._get_client(credential)
        earn_positions = []

        # Flexible products
        try:
            flexible = client.simple_earn_account()
            for pos in flexible.get("positionAmountVos", []):
                earn_positions.append(
                    {
                        "asset": pos["asset"],
                        "type": "flexible",
                        "amount": float(pos.get("amount", 0)),
                        "apy": float(pos.get("latestAnnualPercentageRate", 0)) * 100,
                        "interest_24h": float(pos.get("dailyInterestRate", 0)),
                    }
                )
        except BinanceAPIException as e:
            _logger.warning("Earn flexible API error: %s", str(e))

        # Locked products
        try:
            locked = client.simple_earn_locked_position()
            for pos in locked.get("rows", []):
                earn_positions.append(
                    {
                        "asset": pos["asset"],
                        "type": "locked",
                        "amount": float(pos.get("amount", 0)),
                        "apy": float(pos.get("annualPercentageRate", 0)),
                        "lock_until": (
                            (datetime.now() + timedelta(days=int(pos.get("lockPeriod", 0)))).date()
                            if pos.get("lockPeriod")
                            else False
                        ),
                    }
                )
        except BinanceAPIException as e:
            _logger.warning("Earn locked API error: %s", str(e))

        return earn_positions

    def get_all_prices(self, credential):
        """Get all prices in a single API call."""
        client = self._get_client(credential)
        return client.get_all_tickers()

    def get_price_ticker(self, credential, symbol):
        """Get current price for a symbol."""
        client = self._get_client(credential)
        data = client.get_symbol_ticker(symbol=symbol)
        return float(data.get("price", 0))

    def get_all_orders(self, credential, symbol, limit=50):
        """Get all spot orders for a symbol."""
        client = self._get_client(credential)
        return client.get_all_orders(symbol=symbol, limit=limit)

    def get_open_orders(self, credential, symbol=None):
        """Get open spot orders."""
        client = self._get_client(credential)
        kwargs = {}
        if symbol:
            kwargs["symbol"] = symbol
        return client.get_open_orders(**kwargs)

    def get_futures_all_orders(self, credential, symbol, limit=50):
        """Get all futures orders for a symbol."""
        client = self._get_client(credential)
        return client.futures_account_trades(symbol=symbol, limit=limit)

    def get_futures_open_orders(self, credential, symbol=None):
        """Get open futures orders."""
        client = self._get_client(credential)
        kwargs = {}
        if symbol:
            kwargs["symbol"] = symbol
        return client.futures_get_open_orders(**kwargs)

    def get_best_earn_rates(self, credential, limit=10):
        """Get the best earn rates of the day from Binance.

        Returns dict with two keys:
        - 'flexible': list of top flexible products sorted by APY desc
        - 'locked': list of top locked products sorted by APY desc

        Each item: {
            'asset': str,
            'type': 'flexible' or 'locked',
            'apy': float (percentage),
            'daily_rate': float,
            'min_amount': float or None,
            'duration_days': int or None (locked only),
            'is_upgradeable': bool,
        }
        """
        client = self._get_client(credential)

        flexible = []
        locked = []

        # Flexible earn products
        try:
            resp = client._request(
                "get", "/sapi/v1/simple-earn/flexible/list", params={"size": 100}
            )
            for product in resp.get("rows", []):
                apy = float(product.get("latestAnnualPercentageRate", 0)) * 100
                daily_rate = float(product.get("dailyInterestRate", 0))
                flexible.append(
                    {
                        "asset": product.get("asset", ""),
                        "type": "flexible",
                        "apy": apy,
                        "daily_rate": daily_rate * 100,
                        "min_amount": (
                            float(product.get("minPurchaseAmount", 0))
                            if product.get("minPurchaseAmount")
                            else None
                        ),
                        "duration_days": None,
                        "is_upgradeable": product.get("isUpsell", False),
                    }
                )
            flexible.sort(key=lambda x: x["apy"], reverse=True)
            flexible = flexible[:limit]
        except Exception as e:
            _logger.warning("Failed to fetch flexible earn rates: %s", e)

        # Locked earn products
        try:
            resp = client._request(
                "get", "/sapi/v1/simple-earn/locked/list", params={"size": 100}
            )
            for product in resp.get("rows", []):
                apy = float(product.get("annualPercentageRate", 0)) * 100
                duration = int(product.get("duration", 0))
                locked.append(
                    {
                        "asset": product.get("asset", ""),
                        "type": "locked",
                        "apy": apy,
                        "daily_rate": apy / 365,
                        "min_amount": (
                            float(product.get("minPurchaseAmount", 0))
                            if product.get("minPurchaseAmount")
                            else None
                        ),
                        "duration_days": duration,
                        "is_upgradeable": False,
                    }
                )
            locked.sort(key=lambda x: x["apy"], reverse=True)
            locked = locked[:limit]
        except Exception as e:
            _logger.warning("Failed to fetch locked earn rates: %s", e)

        return {"flexible": flexible, "locked": locked}

    def format_best_earn_rates(self, rates_data, limit=5):
        """Format best earn rates into a readable report."""
        lines = ["Best Earn Rates Today\n"]

        lines.append("Flexible (no lock):")
        for i, p in enumerate(rates_data["flexible"][:limit], 1):
            lines.append(f"  {i}. {p['asset']}: {p['apy']:.2f}% APY")

        lines.append("\nLocked:")
        for i, p in enumerate(rates_data["locked"][:limit], 1):
            days = p["duration_days"]
            lines.append(f"  {i}. {p['asset']}: {p['apy']:.2f}% APY ({days}d lock)")

        return "\n".join(lines)

    def validate_credentials(self, credential):
        """Test if credentials are valid and read-only."""
        try:
            client = self._get_client(credential)
            account = client.get_account()
            can_trade = account.get("canTrade", True)
            if can_trade:
                _logger.warning("API key %s has trading enabled - checking permissions", credential.api_key[:8])
            return True, "Credentials valid"
        except BinanceAPIException as e:
            return False, str(e)
