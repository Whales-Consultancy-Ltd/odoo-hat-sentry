/** @odoo-module **/
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

registry.category("web_tour.tours").add("hat_sentry_dashboard_smoke", {
    url: "/web",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_portfolio_overview']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".o_board:not(:has(.o_loading))",
            timeout: 15000,
        },
    ],
});

registry.category("web_tour.tours").add("hat_sentry_asset_smoke", {
    url: "/web",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_portfolio']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_asset']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".o_list_renderer:not(:has(.o_loading))",
            timeout: 15000,
        },
    ],
});

registry.category("web_tour.tours").add("hat_sentry_snapshot_smoke", {
    url: "/web",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_portfolio']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_portfolio_snapshot']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".o_list_renderer:not(:has(.o_loading))",
            timeout: 15000,
        },
    ],
});

registry.category("web_tour.tours").add("hat_sentry_trade_smoke", {
    url: "/web",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_trading']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_trading_journal']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".o_list_renderer:not(:has(.o_loading))",
            timeout: 15000,
        },
    ],
});

registry.category("web_tour.tours").add("hat_sentry_futures_smoke", {
    url: "/web",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_trading']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_futures_position']",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".o_list_renderer:not(:has(.o_loading))",
            timeout: 15000,
        },
    ],
});
