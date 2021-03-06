# -*- coding: utf-8 -*-
from odoo import models, api

class View(models.Model):
    _inherit = 'ir.ui.view'

    @api.model
    def _prepare_qcontext(self):
        qcontext = super(View, self)._prepare_qcontext()
        website = qcontext.get('website')
        if website:
            acquirer = self.env['payment.acquirer'].sudo()._get_acquirer(company=qcontext['res_company'], website= qcontext['website'], providers=['jetcheckout'], limit=1, raise_exception=False)
            pay_page = acquirer.jetcheckout_payment_page if acquirer else False
            qcontext.update(dict(pay_page=pay_page))
        return qcontext
