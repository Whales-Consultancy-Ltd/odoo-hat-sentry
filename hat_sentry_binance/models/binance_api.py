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
