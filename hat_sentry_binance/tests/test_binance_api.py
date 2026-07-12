from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase


class TestBinanceAPI(TransactionCase):
    def _make_credential(self):
        return self.env["hat_sentry.credential"].create(
            {
                "exchange": "binance",
                "api_key": "test_key",
                "api_secret": "test_secret",
            }
        )

    def _get_api(self):
        return self.env["hat_sentry_binance.api"]

    def test_get_spot_balances(self):
        credential = self._make_credential()
        api = self._get_api()
        mock_client = MagicMock()
        mock_client.get_account.return_value = {
            "balances": [
                {"asset": "BTC", "free": "1.5", "locked": "0.0"},
                {"asset": "USDT", "free": "1000.0", "locked": "0.0"},
            ]
        }
        with patch.object(type(api), "_get_client", return_value=mock_client):
            balances = api.get_spot_balances(credential)
        self.assertEqual(len(balances), 2)
        self.assertEqual(balances[0]["asset"], "BTC")
        self.assertEqual(balances[0]["free"], 1.5)

    def test_get_spot_balances_filters_zero(self):
        credential = self._make_credential()
        api = self._get_api()
        mock_client = MagicMock()
        mock_client.get_account.return_value = {
            "balances": [
                {"asset": "BTC", "free": "1.5", "locked": "0.0"},
                {"asset": "DUST", "free": "0.0", "locked": "0.0"},
            ]
        }
        with patch.object(type(api), "_get_client", return_value=mock_client):
            balances = api.get_spot_balances(credential)
        self.assertEqual(len(balances), 1)
        self.assertEqual(balances[0]["asset"], "BTC")

    def test_get_futures_positions(self):
        credential = self._make_credential()
        api = self._get_api()
        mock_client = MagicMock()
        mock_client.futures_position_information.return_value = [
            {
                "symbol": "BTCUSDT",
                "positionAmt": "0.5",
                "entryPrice": "50000.0",
                "markPrice": "55000.0",
                "leverage": "10",
                "unRealizedProfit": "2500.0",
                "marginType": "isolated",
                "isolatedMargin": "5000.0",
                "liquidationPrice": "45000.0",
            },
        ]
        with patch.object(type(api), "_get_client", return_value=mock_client):
            positions = api.get_futures_positions(credential)
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]["symbol"], "BTCUSDT")
        self.assertEqual(positions[0]["side"], "long")
        self.assertEqual(positions[0]["leverage"], 10.0)
        self.assertEqual(positions[0]["mark_price"], 55000.0)
        self.assertEqual(positions[0]["liquidation_price"], 45000.0)

    def test_validate_credentials_success(self):
        credential = self._make_credential()
        api = self._get_api()
        mock_client = MagicMock()
        mock_client.get_account.return_value = {"canTrade": False}
        with patch.object(type(api), "_get_client", return_value=mock_client):
            valid, msg = api.validate_credentials(credential)
        self.assertTrue(valid)
