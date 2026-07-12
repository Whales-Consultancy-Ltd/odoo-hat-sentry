/** @odoo-module **/
import { markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { stepUtils } from "@web_tour/tour_utils";

registry.category("web_tour.tours").add("hat_sentry_demo_walkthrough", {
    url: "/odoo",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            content: markup(
                _t(
                    "<b>Welcome to Hat Sentry.</b> This is your crypto portfolio control tower, " +
                        "built entirely inside Odoo. Let's take a look around — click to open the app."
                )
            ),
            position: "bottom",
            run: "click",
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_portfolio_overview']",
            content: markup(
                _t(
                    "The <b>Overview dashboard</b> gives you a live snapshot of every exchange " +
                        "you've connected. Click here to see it."
                )
            ),
            position: "bottom",
            run: "click",
        },
        {
            trigger: ".o_board:not(:has(.o_loading))",
            content: markup(
                _t(
                    "This board aggregates your balances across spot, futures, and earn positions " +
                        "in real time. Take a moment to review the widgets before moving on."
                )
            ),
            position: "top",
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_portfolio']",
            content: markup(_t("Now let's look at individual assets. Open the Portfolio menu.")),
            position: "bottom",
            run: "click",
        },
        {
            trigger: ".dropdown-item[data-menu-xmlid='hat_sentry.menu_hat_sentry_asset']",
            content: markup(_t("Click Assets to see each token you hold, valued in real time.")),
            position: "right",
            run: "click",
        },
        {
            trigger: ".o_list_renderer:not(:has(.o_loading)) .o_data_row:first-child",
            content: markup(
                _t(
                    "Here's your first asset. Each row shows quantity, average cost, current price, " +
                        "and unrealized P&L — click a row to see the full detail form."
                )
            ),
            position: "bottom",
            run: "click",
        },
        {
            trigger: ".breadcrumb-item:first-child",
            content: markup(_t("Great — that's the core loop. Let's head back to the dashboard.")),
            position: "bottom",
            run: "click",
        },
        ...stepUtils.goToAppSteps(
            "hat_sentry.menu_hat_sentry_root",
            markup(
                _t(
                    "That's the essentials of Hat Sentry. Explore Alerts and the Trading Journal " +
                        "from the same top menu whenever you're ready."
                )
            )
        ),
    ],
});
