from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestHatSentryTour(HttpCase):
    def test_hat_sentry_smoke(self):
        self.start_tour("/web", "hat_sentry_smoke", login="admin")
