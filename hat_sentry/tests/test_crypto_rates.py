from datetime import date

from odoo.tests.common import TransactionCase


class TestCryptoRates(TransactionCase):
    def setUp(self):
        super().setUp()
        self.CryptoRates = self.env["hat_sentry.crypto.rates"]
        self.CurrencyRate = self.env["res.currency.rate"]
        self.USD = self.env.ref("base.USD")

    def test_update_rate_creates_rate_record(self):
        self.CryptoRates._update_rate(self.USD, 1.0)
        rate = self.CurrencyRate.search(
            [
                ("currency_id", "=", self.USD.id),
                ("name", "=", date.today()),
            ],
            limit=1,
        )
        self.assertTrue(rate)
        self.assertAlmostEqual(rate.rate, 1.0)

    def test_update_rate_with_price(self):
        self.CryptoRates._update_rate(self.USD, 50000.0)
        rate = self.CurrencyRate.search(
            [
                ("currency_id", "=", self.USD.id),
                ("name", "=", date.today()),
            ],
            limit=1,
        )
        self.assertTrue(rate)
        self.assertAlmostEqual(rate.rate, 1.0 / 50000.0)

    def test_update_rate_zero_price_skips_update(self):
        self.CryptoRates._update_rate(self.USD, 0.0)
        rate = self.CurrencyRate.search(
            [
                ("currency_id", "=", self.USD.id),
                ("name", "=", date.today()),
            ],
            limit=1,
        )
        self.assertFalse(rate)

    def test_update_rate_updates_existing(self):
        self.CryptoRates._update_rate(self.USD, 1.0)
        self.CryptoRates._update_rate(self.USD, 2.0)
        rates = self.CurrencyRate.search(
            [
                ("currency_id", "=", self.USD.id),
                ("name", "=", date.today()),
            ]
        )
        self.assertEqual(len(rates), 1)
        self.assertAlmostEqual(rates.rate, 0.5)

    def test_get_crypto_currencies(self):
        currencies = self.CryptoRates._get_crypto_currencies()
        self.assertIn(self.USD, currencies)
