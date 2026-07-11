from odoo import models, fields, api


class HatSentryMarketPrice(models.Model):
    _name = 'hat_sentry.market.price'
    _description = 'Market Price'
    _order = 'date desc, id desc'

    instrument_id = fields.Many2one('hat_sentry.instrument', string='Instrument', required=True, check_company=True)
    date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    price = fields.Float(string='Price', required=True)
    source = fields.Char(string='Source', default='binance')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.ref('base.USD'))
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, check_company=True)

    _sql_constraints = [
        ('unique_price', 'unique(instrument_id, date, source)', 'Price already recorded for this instrument and date!')
    ]
