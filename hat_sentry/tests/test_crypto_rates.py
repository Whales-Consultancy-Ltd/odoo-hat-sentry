from odoo.tests.common import TransactionCase


class TestCryptoRates(TransactionCase):
    def setUp(self):
        super().setUp()
        self.CryptoRates = self.env["hat_sentry.crypto.rates"]
        self.USD = self.env.ref("base.USD")

    def test_asset_defaults_to_usd(self):
        asset = self.env["hat_sentry.asset"].create(
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.assertEqual(asset.currency_id, self.USD)

    def test_stablecoin_defaults_to_usd(self):
        asset = self.env["hat_sentry.asset"].create(
            {
                "symbol": "USDT",
                "name": "Tether",
                "asset_type": "stablecoin",
                "bucket": "stable_reserve",
            }
        )
        self.assertEqual(asset.currency_id, self.USD)

    def test_cron_safe_is_noop(self):
        self.CryptoRates.cron_update_crypto_rates_safe()
