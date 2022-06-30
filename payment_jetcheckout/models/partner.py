# -*- coding: utf-8 -*-
from odoo import fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    def _compute_acquirers(self):
        for partner in self:
            acquirers = self.env['payment.acquirer'].sudo()._get_acquirer(company=self.env.company, providers=['jetcheckout'])
            partner.acquirer_ids = [(6, 0, acquirers.ids)]

    acquirer_ids = fields.Many2many('payment.acquirer', string='Payment Acquirers', compute='_compute_acquirers')
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.campaign', string='PoS Campaign', ondelete='set null', copy=False)
