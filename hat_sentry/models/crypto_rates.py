import logging

from odoo import models

_logger = logging.getLogger(__name__)


class HatSentryCryptoRates(models.AbstractModel):
    _name = "hat_sentry.crypto.rates"
    _description = "Crypto Rates Manager"

    def cron_update_crypto_rates_safe(self):
        """No-op: crypto rates are now stored in hat_sentry.asset, not res.currency.rate.

        This cron is kept as a stub to avoid breaking ir.cron references.
        """
        _logger.info("crypto_rates cron called — res.currency rate updates disabled (issue #24)")
