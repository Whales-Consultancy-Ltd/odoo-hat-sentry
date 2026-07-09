# Hat Sentry — Odoo Crypto Portfolio Control Tower

Hat Sentry is a personal crypto portfolio control tower built as a native **Odoo 19** application. It aggregates exchange data, tracks positions, logs trades, sends alerts, and generates reports — all within a single Odoo instance.

## Modules

| Module | Technical name | Role |
|---|---|---|
| **Core** | `hat_sentry` | Base models, security groups (User/Trader/Manager), shared infrastructure, crypto currency registry |
| **Binance Connector** | `hat_sentry_binance` | Read-only connector for Binance spot, futures, and earn data via scheduled cron jobs |
| **Alerts & Rules** | `hat_sentry_alerts` | Rule engine for price/volume/P&L thresholds with multi-channel notifications |
| **Reports** | `hat_sentry_reports` | QWeb-based daily, weekly, and monthly portfolio PDF reports |
| **Dashboard** | `hat_sentry_dashboard` | Spreadsheet and board dashboards for portfolio overview |
| **Trading Journal** | `hat_sentry_journal` | Behavioral trading journal with mistake tracking and performance analysis |

## Dependencies

- **Odoo 19.0** with standard modules: `base`, `mail`, `digest`, `board`, `base_automation`
- Python packages: `python-binance` (Binance Connector)

## License

LGPL-3 — Business Solutions For Africa
