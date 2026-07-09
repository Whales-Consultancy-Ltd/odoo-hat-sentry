import logging
from datetime import date

from odoo import models

_logger = logging.getLogger(__name__)


class HatSentryCryptoRates(models.AbstractModel):
    _name = "hat_sentry.crypto.rates"
    _description = "Crypto Rates Manager"

    def _get_crypto_currencies(self):
        currency_names = ["BTC", "ETH", "USDT", "BNB", "SOL", "ADA", "XRP", "USDC"]
        return self.env["res.currency"].search([("name", "in", currency_names)])

    def _update_rate(self, currency, price_usdt):
        rate = 1.0 / price_usdt if price_usdt > 0 else 0.0
        existing = self.env["res.currency.rate"].search(
            [
                ("currency_id", "=", currency.id),
                ("name", "=", date.today()),
            ],
            limit=1,
        )
        if existing:
            existing.write({"rate": rate})
        else:
            self.env["res.currency.rate"].create(
                {
                    "currency_id": currency.id,
                    "rate": rate,
                    "name": date.today(),
                }
            )

    def cron_update_crypto_rates(self):
        currencies = self._get_crypto_currencies()
        if not currencies:
            _logger.warning("No crypto currencies found - run module update")
            return

        credential = self.env["hat_sentry.credential"].search(
            [
                ("active", "=", True),
            ],
            limit=1,
        )

        if not credential:
            _logger.warning("No active Binance credentials - cannot update crypto rates")
            return

        api = self.env["hat_sentry_binance.api"]
        for currency in currencies:
            try:
                symbol_map = {
                    "USDT": "USDTUSDT",
                    "USDC": "USDCUSDT",
                }
                if currency.name in symbol_map:
                    symbol = symbol_map[currency.name]
                else:
                    symbol = f"{currency.name}USDT"

                if currency.name == "USDT":
                    price = 1.0
                else:
                    price = api.get_price_ticker(credential, symbol)

                if price > 0:
                    self._update_rate(currency, price)
                    _logger.info(
                        "Updated rate for %s: 1 USD = %.8f %s (price: %.2f USD)",
                        currency.name,
                        1 / price,
                        currency.name,
                        price,
                    )
                else:
                    _logger.warning("Price for %s is 0, skipping", currency.name)
            except Exception as e:
                _logger.error("Failed to update rate for %s: %s", currency.name, str(e))

    def cron_update_crypto_rates_safe(self):
        try:
            self.cron_update_crypto_rates()
        except Exception as e:
            _logger.error("Crypto rates cron failed: %s", str(e))
