from odoo.tests.common import TransactionCase


class TestAsset(TransactionCase):
    def setUp(self):
        super().setUp()
        self.USD = self.env.ref("base.USD")
        self.Asset = self.env["hat_sentry.asset"]

    def test_create_crypto_asset(self):
        asset = self.Asset.create(
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.assertEqual(asset.symbol, "BTC")
        self.assertEqual(asset.asset_type, "crypto")
        self.assertEqual(asset.bucket, "core")
        self.assertTrue(asset.active)

    def test_is_stablecoin_false_for_crypto(self):
        crypto = self.Asset.create(
            {
                "symbol": "ETH",
                "name": "Ethereum",
                "asset_type": "crypto",
                "bucket": "trading",
            }
        )
        self.assertFalse(crypto.is_stablecoin)

    def test_is_stablecoin_true_for_stablecoin(self):
        stable = self.Asset.create(
            {
                "symbol": "USDT",
                "name": "Tether",
                "asset_type": "stablecoin",
                "bucket": "stable_reserve",
            }
        )
        self.assertTrue(stable.is_stablecoin)

    def test_is_core_asset_true_for_core(self):
        core = self.Asset.create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.assertTrue(core.is_core_asset)

    def test_is_core_asset_false_for_trading(self):
        trading = self.Asset.create(
            {
                "symbol": "ETH",
                "asset_type": "crypto",
                "bucket": "trading",
            }
        )
        self.assertFalse(trading.is_core_asset)

    def test_open_position_count_zero_when_no_positions(self):
        asset = self.Asset.create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.assertEqual(asset.open_position_count, 0)

    def test_ensure_currency_usdt_maps_to_usd(self):
        currency = self.Asset._ensure_currency("USDT")
        self.assertEqual(currency, self.USD)

    def test_ensure_currency_usdc_maps_to_usd(self):
        currency = self.Asset._ensure_currency("USDC")
        self.assertEqual(currency, self.USD)

    def test_ensure_currency_creates_new(self):
        currency = self.Asset._ensure_currency("BTC")
        self.assertEqual(currency.name, "BTC")
        self.assertTrue(currency.active)

    def test_ensure_currency_truncates_long_symbols(self):
        currency = self.Asset._ensure_currency("SOLANA")
        self.assertEqual(currency.name, "SOL")

    def test_active_toggle(self):
        asset = self.Asset.create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.assertTrue(asset.active)
        asset.active = False
        self.assertFalse(asset.active)

    def test_invalid_bucket_raises_validation_error(self):
        with self.assertRaises(ValueError):
            self.Asset.create(
                {
                    "symbol": "XRP",
                    "asset_type": "crypto",
                    "bucket": "invalid_bucket",
                }
            )

    def test_trade_count_zero_when_no_trades(self):
        asset = self.Asset.create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.assertEqual(asset.trade_count, 0)

    def test_total_trade_pnl_zero_when_no_trades(self):
        asset = self.Asset.create(
            {
                "symbol": "BTC",
                "asset_type": "crypto",
                "bucket": "core",
            }
        )
        self.assertEqual(asset.total_trade_pnl, 0.0)
