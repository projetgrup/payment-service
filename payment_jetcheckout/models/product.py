# -*- coding: utf-8 -*-
import json
import requests

from odoo import models, fields, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _sanitize_vals(self, vals):
        super(ProductTemplate, self)._sanitize_vals(vals)
        if 'base_unit_count' in self._fields and ('base_unit_count' not in vals or not vals['base_unit_count']):
            vals['base_unit_count'] = 0


class ProductCategory(models.Model):
    _inherit = 'product.category'

    jetcheckout_credit_categ_id = fields.Many2one('product.category.jetcheckout.credit')

    def update_jetcheckout_credit_categ(self):
        acquirer = self.env['payment.acquirer']._get_acquirer(providers=['jetcheckout'])
        if not acquirer:
            raise UserError(_('Paylox Payment Acquirer cannot be found related to this company.'))

        url = '%s/api/v1/prepayment/sc_itemcategories' % acquirer._get_paylox_api_url()
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "language": "tr",
        }
  
        categs = []
        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if result['response_code'] == "00":
                for categ in result['categories']:
                    categs.append({
                        'code': categ['id'],
                        'name': categ['name'],
                        'desc': categ['description'],
                    })
        if not categs:
            raise UserError(_('Shopping credit categories cannot be pulled from Paylox gateway service.'))

        categs = {
            categ['code']: {
                'code': categ['code'],
                'name': categ['name'],
                'desc': categ['desc'],
            } for categ in categs
        }
        categs_all = self.env['product.category.jetcheckout.credit'].sudo().search([])
        for categ in categs_all:
            if categ['code'] not in categs:
                categ.unlink()
            else:
                categ.write({
                    'name': categ['name'],
                    'desc': categ['desc'],
                })
                del categs[categ['code']]
        if categs:
            categs_all.create([{
                'code': categ['code'],
                'name': categ['name'],
                'desc': categ['desc'],
            } for categ in categs.values()])


class ProductCategoryJetcheckoutCredit(models.Model):
    _name = 'product.category.jetcheckout.credit'
    _description = 'Paylox Shopping Credit Product Category'

    name = fields.Char()
    desc = fields.Char()
    code = fields.Integer()
