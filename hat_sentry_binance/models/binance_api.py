import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta

import requests
from odoo import models

_logger = logging.getLogger(__name__)


class BinanceAPI(models.AbstractModel):
    _name = "hat_sentry_binance.api"
    _description = "Binance API Client"

    BASE_URL = "https://api.binance.com"
    FUTURES_URL = "https://fapi.binance.com"

    def _get_headers(self, credential):
        """Generate headers for Binance API call."""
        return {
            "X-MBX-APIKEY": credential.api_key,
            "Content-Type": "application/json",
        }

    def _sign_request(self, credential, params):
        """Sign params with HMAC-SHA256."""
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            credential.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return signature

    def _call_api(self, credential, endpoint, params=None, base_url=None):
        """Make a signed GET request to Binance API."""
        if base_url is None:
            base_url = self.BASE_URL
        if params is None:
            params = {}
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign_request(credential, params)

        url = f"{base_url}{endpoint}"
        headers = self._get_headers(credential)

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            _logger.info("Binance API call: %s (status %s)", endpoint, response.status_code)
            return response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            _logger.error("Binance API error: %s - %s", endpoint, str(e))
            raise

    def get_spot_balances(self, credential):
        """Get all spot balances. Returns list of dicts."""
        data = self._call_api(credential, "/api/v3/account")
        balances = []
        for balance in data.get("balances", []):
            free = float(balance.get("free", 0))
            locked = float(balance.get("locked", 0))
            if free > 0 or locked > 0:
                balances.append(
                    {
                        "asset": balance["asset"],
                        "free": free,
                        "locked": locked,
                    }
                )
        return balances

    def get_futures_positions(self, credential):
        """Get all open futures positions. Returns list of dicts."""
        data = self._call_api(credential, "/fapi/v2/account", base_url=self.FUTURES_URL)
        positions = []
        for pos in data.get("positions", []):
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
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        data = self._call_api(credential, "/fapi/v1/fundingRate", params=params, base_url=self.FUTURES_URL)
        return data

    def get_earn_positions(self, credential):
        """Get Earn positions (flexible + locked)."""
        earn_positions = []
        # Flexible products
        try:
            flexible = self._call_api(credential, "/sapi/v1/simple-earn/account")
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
        except Exception as e:
            _logger.warning("Earn flexible API error: %s", str(e))

        # Locked products
        try:
            locked = self._call_api(credential, "/sapi/v1/simple-earn/locked/position")
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
        except Exception as e:
            _logger.warning("Earn locked API error: %s", str(e))

        return earn_positions

    def get_all_prices(self, credential):
        """Get all prices in a single API call."""
        return self._call_api(credential, "/api/v3/ticker/price")

    def get_price_ticker(self, credential, symbol):
        """Get current price for a symbol."""
        data = self._call_api(credential, "/api/v3/ticker/price", params={"symbol": symbol})
        return float(data.get("price", 0))

    def validate_credentials(self, credential):
        """Test if credentials are valid and read-only."""
        try:
            data = self._call_api(credential, "/api/v3/account")
            can_trade = data.get("canTrade", True)
            if can_trade:
                _logger.warning("API key %s has trading enabled - checking permissions", credential.api_key[:8])
            return True, "Credentials valid"
        except Exception as e:
            return False, str(e)
