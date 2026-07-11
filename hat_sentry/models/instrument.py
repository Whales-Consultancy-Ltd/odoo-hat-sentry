from odoo import models, fields, api


class HatSentryInstrument(models.Model):
    _name = 'hat_sentry.instrument'
    _description = 'Trading Instrument'

    name = fields.Char(string='Name', required=True)
    symbol = fields.Char(string='Symbol', required=True)
    base_asset_id = fields.Many2one('hat_sentry.asset', string='Base Asset', required=True)
    quote_asset_id = fields.Many2one('hat_sentry.asset', string='Quote Asset', required=True)
    market_type = fields.Selection([
        ('spot', 'Spot'),
        ('futures_usdm', 'USD-M Futures'),
        ('futures_coinm', 'COIN-M Futures'),
    ], string='Market Type', required=True, default='spot')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
