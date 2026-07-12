from odoo import api, fields, models


class HatSentrySetupWizard(models.TransientModel):
    _name = "hat_sentry.setup.wizard"
    _description = "Hat Sentry Setup Wizard"

    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=lambda self: self.env.company,
    )
    exchange = fields.Selection([("binance", "Binance")], string="Exchange", required=True, default="binance")
    api_key = fields.Char(string="API Key", required=True)
    api_secret = fields.Char(string="API Secret", required=True)
    test_result = fields.Char(string="Test Result", readonly=True)
    test_success = fields.Boolean(string="Test Success", readonly=True)

    def action_test_connection(self):
        """Test the API credentials."""
        self.ensure_one()
        try:
            credential = self.env["hat_sentry.credential"].create({
                "exchange": self.exchange,
                "api_key": self.api_key,
                "api_secret": self.api_secret,
                "company_id": self.company_id.id,
            })
            api = self.env["hat_sentry_binance.api"]
            success, message = api.validate_credentials(credential)
            self.test_result = message
            self.test_success = success
            credential.unlink()
        except Exception as e:
            self.test_result = str(e)
            self.test_success = False
        # Return action to reload the wizard and keep it open
        return {
            "type": "ir.actions.act_window",
            "res_model": "hat_sentry.setup.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "views": [(False, "form")],
            "target": "new",
        }

    def action_save(self):
        """Save the credentials."""
        self.ensure_one()
        self.env["hat_sentry.credential"].create({
            "exchange": self.exchange,
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "company_id": self.company_id.id,
        })
        return {"type": "ir.actions.act_window_close"}
