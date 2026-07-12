from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase


class TestBinanceAPI(TransactionCase):
    @patch("binance.client.Client")
    def test_get_spot_balances(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_account.return_value = {
            "balances": [
                {"asset": "BTC", "free": "1.5", "locked": "0.0"},
                {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
            ]
        }
        credential = self.env["hat_sentry.credential"].create(
            {
                "exchange": "binance",
                "api_key": "test_key",
                "api_secret": "test_secret",
            }
        )
        api = self.env["hat_sentry_binance.api"]
        balances = api.get_spot_balances(credential)
        self.assertEqual(len(balances), 2)
        self.assertEqual(balances[0]["asset"], "BTC")
        self.assertEqual(balances[0]["free"], 1.5)

    @patch("binance.client.Client")
    def test_get_spot_balances_filters_zero(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_account.return_value = {
            "balances": [
                {"asset": "BTC", "free": "1.5", "locked": "0.0"},
                {"asset": "DUST", "free": "0.0", "locked": "0.0"},
            ]
        }
        credential = self.env["hat_sentry.credential"].create(
            {
                "exchange": "binance",
                "api_key": "test_key",
                "api_secret": "test_secret",
            }
        )
        api = self.env["hat_sentry_binance.api"]
        balances = api.get_spot_balances(credential)
        self.assertEqual(len(balances), 1)
        self.assertEqual(balances[0]["asset"], "BTC")

    @patch("binance.client.Client")
    def test_get_futures_positions(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.futures_account.return_value = {
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "positionAmt": "0.5",
                    "entryPrice": "50000.0",
                    "markPrice": "55000.0",
                    "leverage": "10",
                    "unrealizedProfit": "2500.0",
                    "isolated": True,
                    "isolatedWallet": "5000.0",
                    "liquidationPrice": "45000.0",
                },
            ]
        }
        credential = self.env["hat_sentry.credential"].create(
            {
                "exchange": "binance",
                "api_key": "test_key",
                "api_secret": "test_secret",
            }
        )
        api = self.env["hat_sentry_binance.api"]
        positions = api.get_futures_positions(credential)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["symbol"], "BTCUSDT")
        self.assertEqual(positions[0]["side"], "long")
        self.assertEqual(positions[0]["leverage"], 10.0)

    @patch("binance.client.Client")
    def test_validate_credentials_success(self, mock_client_class):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.get_account.return_value = {"canTrade": False}
        credential = self.env["hat_sentry.credential"].create(
            {
                "exchange": "binance",
                "api_key": "test_key",
                "api_secret": "test_secret",
            }
        )
        api = self.env["hat_sentry_binance.api"]
        valid, msg = api.validate_credentials(credential)
        self.assertTrue(valid)
