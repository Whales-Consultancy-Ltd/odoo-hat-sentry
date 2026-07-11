/** @odoo-module **/
import { registry } from "@web/core/registry";
import { stepUtils } from "@web_tour/tour_utils";

registry.category("web_tour.tours").add("hat_sentry_smoke", {
    url: "/web",
    steps: () => [
        stepUtils.showAppsMenuItem(),
        {
            trigger: ".o_app[data-menu-xmlid='hat_sentry.menu_hat_sentry_root']",
            run: "click",
            timeout: 30000,
        },
        {
            trigger: ".o_action_manager",
            timeout: 15000,
        },
    ],
});
