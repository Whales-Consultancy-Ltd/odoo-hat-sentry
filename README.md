# Hat Sentry — Odoo Crypto Portfolio Control Tower

Hat Sentry is a personal crypto portfolio control tower built as a native
**Odoo 19** application. It aggregates exchange data, tracks positions, logs
trades, sends alerts, and generates reports — all within a single Odoo
instance.

## Modules

| Module | Technical name | Role |
|--------|----------------|------|
| Core | `hat_sentry` | Base models, security, crypto registry |
| Binance Connector | `hat_sentry_binance` | Connector for spot, futures, earn |
| Alerts & Rules | `hat_sentry_alerts` | Rule engine, notifications |
| Reports | `hat_sentry_reports` | PDF reports (daily/weekly/monthly) |
| Dashboard | `hat_sentry_dashboard` | Spreadsheet and board dashboards |
| Trading Journal | `hat_sentry_journal` | Journal with mistake tracking |

## Dependencies

- **Odoo 19.0** with: `base`, `mail`, `digest`, `board`, `base_automation`
- Python packages: `requests` (Binance Connector uses raw HTTP + HMAC signing)

## License

LGPL-3 — Business Solutions For Africa
