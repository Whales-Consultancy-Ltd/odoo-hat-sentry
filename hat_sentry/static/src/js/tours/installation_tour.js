/** @odoo-module **/
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

registry.category("web_tour.tours").add("hat_sentry_installation_tour", {
    url: "/odoo",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            content: "Open Hat Sentry — your crypto portfolio control tower",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_portfolio']",
            content: "Open Portfolio section",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_asset']",
            content: "View your crypto assets",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".o_list_renderer:not(:has(.o_loading))",
            content: "Asset list view renders correctly",
            timeout: 15000,
        },
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            content: "Go back to Hat Sentry menu",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_trading']",
            content: "Open Trading section",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_futures_position']",
            content: "View futures positions",
            run: "click",
            timeout: 15000,
        },
        {
            trigger: ".o_list_renderer:not(:has(.o_loading))",
            content: "Futures position list view renders correctly",
            timeout: 15000,
        },
    ],
});
