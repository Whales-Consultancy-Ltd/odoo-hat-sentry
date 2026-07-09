{
    "name": "Hat Sentry — Binance Connector",
    "version": "19.0.1.0.0",
    "category": "Hat Sentry",
    "summary": "Binance read-only connector — spot, futures, earn data collection",
    "description": """
Read-only connector for Binance exchange.
Collects spot balances, futures positions, funding rates, and earn positions.
No trading orders are placed, modified, or cancelled.
    """,
    "author": "Business Solutions For Africa",
    "website": "https://www.biz4africa.com",
    "license": "LGPL-3",
    "depends": ["hat_sentry"],
    "data": [
        "data/binance_cron.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "external_dependencies": {"python": ["requests"]},
}
