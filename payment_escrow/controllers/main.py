# -*- coding: utf-8 -*-
from odoo import _
from odoo.http import route, request
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller


class CustomerPortal(portal.CustomerPortal):

    @route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            return request.redirect('/my/ads')
        return super().home(**kwargs)


class PayloxSystemEscrowController(Controller):

    def _get_tx_values(self, **kwargs):
        return {
            'paylox_description': kwargs.get('description', False),
            'jetcheckout_payment_ok': kwargs.get('payment_ok', True),
        }

    def _get_tx_values(self, **kwargs):
        res = super()._get_tx_values(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            res.update({
                'jetcheckout_approval_ok': True,
            })
        return res

    def _get_data_values(self, data, transaction, **kwargs):
        values = super()._get_data_values(data, transaction, **kwargs)
        if transaction and transaction.system == 'escrow':
            partner = transaction.paylox_product_ids[0]['product_id']['owner_id']
            reference = partner.bank_ids and partner.bank_ids[0]['api_ref']
            if not reference:
                raise ValidationError(_('%s must have at least one bank account which is verified.' % partner.name))

            if transaction.company_id.payment_page_token_wo_commission:
                amount = float_round(transaction.amount * (1 - (transaction.jetcheckout_commission_rate / 100)), 4)
            else:
                amount = float(kwargs['amount'])

            values.update({
                'is_submerchant_payment': True,
                'submerchant_external_id': reference,
                'submerchant_price': amount,
            })
        return values

    @route('/my/ads', type='http', auth='user', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_my_ads(self, **kwargs):
        company = request.env.company
        user = request.env.user
        partner = user.partner_id
        domain = [('company_id', '=', company.id)]
        if user.share:
            domain.append(('broker_id', '=', partner.id))
        ads = request.env['product.product'].sudo().with_context(system='escrow').search(domain)
        values = {
            'ads': ads,
            'partner': partner,
            'company': company,
            'currency': company.currency_id,
        }
        return request.render('payment_escrow.page_ads', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @route(['/my/ad/<int:id>/image'], type='http', auth='user')
    def page_my_ad_image(self, id):
        return request.env['ir.http'].sudo()._content_image(xmlid=None, model='product.product', res_id=id, field='image_1920', filename_field='name', unique=None, filename=None, mimetype=None, download=None, width=0, height=0, crop=False, quality=0, access_token=None)

    @route(['/my/ad/save'], type='json', auth='user', website=True)
    def page_my_ad_save(self, **kwargs):
        product = request.env['product.product'].sudo().with_context(system='escrow').search([
            ('id', '=', kwargs['id']),
            ('broker_id', '=', request.env.user.partner_id.id),
            ('company_id', '=', request.env.company.id),
        ])
        if not product:
            return {'error': _('Product cannot be found, or you are not allowed to save it.')}

        values = {}
        if 'name' in kwargs and product.name != kwargs['name']:
            values.update({'name': kwargs['name']})
        if 'categ' in kwargs and product.categ_id.id != kwargs['categ']:
            values.update({'categ_id': kwargs['categ']})
        if 'price' in kwargs and product.name != kwargs['price']:
            values.update({'price': kwargs['price']})
        if 'desc' in kwargs and product.description != kwargs['desc']:
            values.update({'description': kwargs['desc']})
        if 'img' in kwargs and product.image_1920 != kwargs['img']:
            values.update({'image_1920': kwargs['img']})
        if values:
            product.write(values)

        return {
            'id': product.id,
        }
