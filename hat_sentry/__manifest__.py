{
    "name": "Hat Sentry — Core",
    "version": "19.0.1.0.0",
    "category": "Hat Sentry",
    "summary": "Crypto portfolio control tower — core models, security, base infrastructure",
    "description": "Hat Sentry is a personal crypto control tower built as a native "
                   "Odoo app. This core module provides the base models, security "
                   "groups, and shared infrastructure.",
    "author": "Business Solutions For Africa",
    "website": "https://www.biz-africa.com/",
    "license": "LGPL-3",
    "depends": ["base", "mail", "digest", "board", "base_automation"],
    "external_dependencies": {"python": ["requests", "markupsafe"]},
    "data": [
        "security/hat_sentry_groups.xml",
        "security/hat_sentry_security.xml",
        "security/ir.model.access.csv",
        "data/crypto_currencies.xml",
        "data/crypto_rates_cron.xml",
        "data/digest_data.xml",
        "data/tour_data.xml",
        "views/settings_views.xml",
        # action-defining files first (no %(xml_id)d deps)
        "views/portfolio_snapshot_views.xml",
        "views/balance_views.xml",
        "views/futures_position_views.xml",
        "views/funding_event_views.xml",
        "views/earn_position_views.xml",
        "views/alert_views.xml",
        "views/credential_views.xml",
        "views/mistake_tag_views.xml",
        # files that reference actions via %(xml_id)d — must come after
        "views/asset_views.xml",
        "views/dashboard_views.xml",
        # menus last (action="xml_id" resolves at runtime)
        "views/menus.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "hat_sentry/static/src/js/tours/**/*",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}
