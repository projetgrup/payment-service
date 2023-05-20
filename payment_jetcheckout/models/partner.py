# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _get_acquirers(self, partner=None, limit=None):
        company = partner and partner.company_id or self.env.company
        return self.env['payment.acquirer'].sudo()._get_acquirer(company=company, providers=['jetcheckout'], limit=limit, raise_exception=False)

    def _compute_acquirers(self):
        for partner in self:
            acquirers = self._get_acquirers(partner)
            partner.acquirer_ids = [(6, 0, acquirers.ids)]
   
    def _default_campaign_id(self):
        partner = False
        active_id = self.env.context.get('active_id')
        if active_id:
            partner = self.browse(active_id)

        acquirers = self._get_acquirers(partner, limit=1)
        if acquirers:
            return acquirers.jetcheckout_campaign_id.id
        return False

    acquirer_ids = fields.Many2many('payment.acquirer', string='Payment Acquirers', compute='_compute_acquirers')
    campaign_id = fields.Many2one('payment.acquirer.jetcheckout.campaign', string='PoS Campaign', ondelete='set null', default=_default_campaign_id, copy=False)
