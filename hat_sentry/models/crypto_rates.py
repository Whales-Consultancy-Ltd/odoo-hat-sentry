import logging
from datetime import date

from odoo import models

_logger = logging.getLogger(__name__)


class HatSentryCryptoRates(models.AbstractModel):
    _name = "hat_sentry.crypto.rates"
    _description = "Crypto Rates Manager"

    def _get_crypto_currencies(self):
        """Get all active res.currency records."""
        return self.env["res.currency"].search([("active", "=", True)])

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
            _logger.warning("No active currencies found")
            return

        credential = self.env["hat_sentry.credential"].search(
            [("active", "=", True)],
            limit=1,
        )
        if not credential:
            _logger.warning("No active Binance credentials - cannot update crypto rates")
            return

        api = self.env["hat_sentry_binance.api"]
        for currency in currencies:
            try:
                self._update_single_rate(currency, api, credential)
            except Exception as e:
                _logger.warning("Failed to update rate for %s: %s", currency.name, str(e))

    def _update_single_rate(self, currency, api, credential):
        """Update rate for a single currency. Skips gracefully if price unavailable.

        Stablecoin symbols (USDT, USDC) are mapped to USD — no rate update needed.
        """
        # Skip fiat currencies
        if currency.name in ("USD", "EUR", "GBP", "CHF", "JPY", "CAD", "AUD"):
            return
        # Skip stablecoins mapped to USD
        if currency.id == self.env.ref("base.USD", raise_if_not_found=False).id:
            return

        symbol = f"{currency.symbol or currency.name}USDT"
        try:
            price = api.get_price_ticker(credential, symbol)
        except Exception:
            _logger.debug("No price for %s (%s), skipping", currency.name, symbol)
            return

        if price and price > 0:
            self._update_rate(currency, price)
            _logger.info(
                "Updated rate for %s: 1 USD = %.8f %s (price: %.2f USD)",
                currency.name,
                1 / price,
                currency.name,
                price,
            )

    def cron_update_crypto_rates_safe(self):
        try:
            self.cron_update_crypto_rates()
        except Exception as e:
            _logger.error("Crypto rates cron failed: %s", str(e))
