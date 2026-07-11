odoo.define('hat_sentry.tour', function(require) {
    'use strict';
    const tour = require('web_tour.tour');
    tour.register('hat_sentry_onboarding', {test: true, url: '/web'}, [
        {content: 'Open Hat Sentry app', trigger: '.o_app[data-menu-xmlid="hat_sentry.menu_hat_sentry_root"]'},
        {content: 'Navigate to Portfolio', trigger: '.o_menu_item a:contains("Portfolio")'},
        {content: 'View Assets', trigger: '.o_menu_item a:contains("Assets")'},
        {content: 'Check list loaded', trigger: '.o_list_view'},
    ]);
});
