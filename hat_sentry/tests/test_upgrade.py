from odoo.tests.common import TransactionCase


class TestUpgrade(TransactionCase):
    def test_module_installs(self):
        module = self.env["ir.module.module"].search(
            [("name", "=", "hat_sentry")], limit=1
        )
        self.assertTrue(module, "hat_sentry module not found")
        self.assertIn(
            module.state,
            ["installed", "to upgrade"],
            "Module not installed",
        )
