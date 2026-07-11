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

## Installation

### Prerequisites

- **Odoo 19.0** (community or enterprise)
- Python 3.12+
- pip packages: `requests`, `markupsafe`, `python-binance`

### Steps

1. Clone this repository into your Odoo addons path:

```bash
git clone https://github.com/TheRealHatCoder/the-hat-sentry.git /path/to/odoo/addons/the-hat-sentry
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Add the repository root to your Odoo `addons_path` in `odoo.conf`:

```ini
addons_path = /path/to/odoo/addons,/path/to/odoo/addons/the-hat-sentry
```

4. Restart Odoo and install **Hat Sentry — Core** from the Apps menu. The
   sub-modules (Binance, Alerts, Journal, Dashboard, Reports) can be
   installed individually after the core module.

## Configuration

### Binance API Setup

1. Go to **Hat Sentry > Configuration > Credentials**
2. Click **Create** and fill in:
   - **Name**: a label for this credential (e.g. "Binance Main")
   - **Exchange**: select `binance`
   - **API Key**: your Binance API key
   - **API Secret**: your Binance API secret
3. Click **Test Connection** to verify

### Binance API Permissions

The connector is **read-only**. Create your API key with these settings:

| Permission | Required |
|------------|----------|
| Enable Reading | Yes |
| Enable Spot & Margin Trading | **No** |
| Enable Futures | **No**
| Enable Withdrawals | **No** |
| IP Restriction | **Strongly recommended** |

Restrict the API key to your server IP. Never use an API key with trading
or withdrawal permissions.

### Security Matrix

| Group | Access |
|-------|--------|
| `hat_sentry_group_user` | View own assets, snapshots, balances |
| `hat_sentry_group_manager` | Full CRUD on all portfolio objects |
| Company rule | All records filtered by `company_id` |

Record rules enforce company-level isolation. Users can only see records
belonging to their company.

## Troubleshooting

### "No module named 'binance'"

Install the Python package:

```bash
pip install python-binance
```

### "APIError -1022 Signature invalid"

Check that your system clock is synchronized. Binance rejects requests with
timestamps more than 5 seconds off.

```bash
sudo ntpdate pool.ntp.org
```

### "No journal could be found" (tests)

When running tests, ensure the purchase/sale journals exist:

```python
self.env["account.journal"].create({
    "name": "Purchase", "type": "purchase",
    "code": "PUR", "company_id": self.env.company.id,
})
```

### Cron jobs not running

Verify that Odoo's cron workers are active:

```bash
./odoo-bin --workers=4  # non-cron workers enable cron processing
```

Or run cron manually:

```bash
./odoo-bin --cron --stop-after-init -d your_database
```

### Dashboard not loading

The `board` module must be installed. It is a dependency of
`hat_sentry_dashboard` and should install automatically.

## CI Pipeline

The repository includes a GitHub Actions CI pipeline (`.github/workflows/ci.yml`)
that runs on every push and PR to `19.0`:

- **lint**: `ruff`, `pylint-odoo`, `bandit`
- **validate**: XML well-formedness + Python AST parsing for all modules

## License

LGPL-3 — Business Solutions For Africa
