# -*- coding: utf-8 -*-
import werkzeug
import json
import requests
import uuid
import base64
import hashlib
from odoo import http, SUPERUSER_ID, _
from odoo.http import request
from odoo.tools.misc import formatLang, get_lang
from odoo.tools.float_utils import float_compare
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class jetcheckoutController(http.Controller):

    def jetcheckout_get_acquirer(self, providers=None, limit=None):
        domain = [('state', 'in', ('enabled', 'test'))]
        if providers:
            domain.append(('provider', 'in', providers))
        if request.env['res.company'].search_count([]) > 1:
            domain.append(('company_id','=',request.env.company.id))
        if request.env['website'].search_count([]) > 1:
            domain.append(('website_id','=',request.website.id))
        acquirer = request.env['payment.acquirer'].sudo().search(domain, limit=limit, order='sequence')
        if not acquirer:
            raise ValidationError(_('Payment acquirer not found. Please contact with system administrator'))
        return acquirer

    def jetcheckout_get_partner(self, **kwargs):
        return 'partner_id' in kwargs and int(kwargs['partner_id']) or request.env.user.partner_id.commercial_partner_id.id

    def jetcheckout_tx_vals(self, **kwargs):
        return {}

    def jetcheckout_get_data(self, acquirer=False, company=False, transaction=False, balance=True):
        if not acquirer:
            acquirer = self.jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        company = company or request.env.company
        currency = transaction and transaction.currency_id or company.currency_id
        lang = get_lang(request.env)
        partner = request.env.user.partner_id
        partner_commercial = partner.commercial_partner_id
        partner_contact = partner if partner.parent_id else False
        card_family = self.jetcheckout_get_card_family(acquirer)

        vals = {
            'partner_id': partner_commercial.id,
            'partner_name': partner_commercial.name,
            'contact': partner_contact.id if partner_contact else False,
            'contact_name': partner_contact.name if partner_contact else False,
            'acquirer': acquirer,
            'company': company,
            'card_family': card_family,
            'currency': {
                'self' : currency,
                'id' : currency.id,
                'name' : currency.name,
                'decimal' : currency.decimal_places,
                'symbol' : currency.symbol,
                'position' : currency.position,
                'separator' : lang.decimal_point,
                'thousand' : lang.thousands_sep,
            },
        }
        if balance:
            balance = partner_commercial.credit-partner_commercial.debit
            balance_str = formatLang(request.env, abs(balance), currency_obj=currency)
            balance_sign = float_compare(balance, 0.0, precision_rounding=currency.rounding) < 0
            vals.update({
                'balance': balance,
                'partner_balance': balance_str,
                'partner_balance_sign': balance_sign,
                'partner_balance_sign_str': balance_sign and _('Credit')[0] or _('Debit')[0],
                'partner_balance_sign_title': balance_sign and _('Credit') or _('Debit'),
            })
        return vals

    def jetcheckout_get_installment_data(self, acquirer=False, **kwargs):
        if not acquirer:
            acquirer = self.jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        currency = request.env.company.currency_id
        bin_number = kwargs['cardnumber'][:6] if len(kwargs['cardnumber']) >= 6 else False
        prefix = kwargs.get('prefix', '')
        url = '%s/api/v1/prepayment/%sinstallment_options' % (acquirer._get_jetcheckout_api_url(), prefix)
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_jetcheckout_env(),
            "language": "tr",
            "currency": currency.name,
            "campaign_name": "",
            "is_3d": True,
        }
        if prefix:
            data.update({"bin": bin_number})

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if int(result['response_code']) == 0:
                installments = []
                amount = kwargs.get('amount', 0)
                amount_installment = kwargs.get('amount_installment', 0)
                installment_options = result.get('installment_options', result.get('installments', []))
                for options in installment_options:
                    installment_list = []
                    for installment in options['installments']:
                        if amount_installment > 0 and amount > 0 and installment['installment_count'] != 1:
                            #customer_rate = (100 * amount_installment / amount) - 100
                            #if installment['customer_rate']:
                            #    installment['customer_rate'] = (2 * (installment['customer_rate'] + customer_rate)) + (installment#['customer_rate'] * customer_rate / 100)
                            #else:
                            #    installment['customer_rate'] = customer_rate
                            installment['customer_rate'] += (100 * amount_installment / amount) - 100
                        installment['total_installment'] = int(installment['installment_count']) + installment['plus_installment']
                        installment_list.append(installment)
                    installment_list.sort(key=lambda x: int(x['installment_count']))
                    installments.append(options)

                values = {
                    'installments': installments,
                    'amount':amount,
                    'currency': currency,
                    's2s_form': kwargs.get('s2s', False)
                }
            elif int(result['response_code']) == 104:
                values = {
                    'installments': [{
                        "card_family": "",
                        "card_family_logo": "",
                        "installments": [{
                            "installment_count": 1,
                            "cost_rate": 0.0,
                            "customer_rate": 0.0,
                            "plus_installment": 0,
                            "plus_installment_description": "",
                            "total_installment": 1
                        }]
                    }],
                    'amount': kwargs['amount'],
                    'currency': currency,
                    's2s_form': kwargs.get('s2s', False)
                }
            else:
                values = {'error': _('%s (Error Code: %s)') % (result['message'], result['response_code'])}
        else:
            values = {'error': _('%s (Error Code: %s)') % (response.reason, response.status_code)}
        return values

    def jetcheckout_get_card_family(self, acquirer=False, **kwargs):
        if not acquirer:
            acquirer = self.jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        currency = request.env.company.currency_id
        url = '%s/api/v1/prepayment/installment_options' % acquirer._get_jetcheckout_api_url()
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_jetcheckout_env(),
            "language": "tr",
            "currency": currency.name,
            "campaign_name": "",
            "is_3d": True,
        }

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if int(result['response_code']) == 0:
                installments = result.get('installment_options', [])
                card_family = []
                for installment in installments:
                    card_family.append(installment['card_family_logo'])
                return card_family
            else:
                return []
        else:
            return []

    def jetcheckout_get_fees(self, acquirer=False, **kwargs):
        kwargs['prefix'] = 'bin_'
        values = self.jetcheckout_get_installment_data(acquirer=acquirer, **kwargs)
        if 'error' in values:
            return values
        installments = filter(lambda x: x['installment_count'] == kwargs['installment'] ,values['installments'][0]['installments'])
        for installment in installments:
            return float(installment.get('customer_rate', 0.0))
        return 0.0

    def jetcheckout_payment_simulation(self, url, data):
        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if int(result['response_code']) == 0:
                return result.get('virtual_pos_name', '-').split(' - ', 1)[1], result.get('expected_cost_rate', 0)
            else:
                return {'error': _('%s (Error Code: %s)') % (result['message'], result['response_code'])}, None
        else:
            return {'error': _('%s (Error Code: %s)') % (response.reason, response.status_code)}, None

    def jetcheckout_process(self, **kwargs):
        if 'order_id' not in kwargs:
            return werkzeug.utils.redirect('/404')

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',kwargs.get('order_id'))], limit=1)
        if not tx:
            return werkzeug.utils.redirect('/404')

        if int(kwargs.get('response_code')) == 0:
            tx.write({'state': 'done'})
            if hasattr(tx, 'sale_order_ids') and tx.sale_order_ids:
                tx.jetcheckout_validate_order()
            tx.jetcheckout_payment()
        else:
            tx.write({
                'state': 'error',
                'state_message': _('%s (Error Code: %s)') % (kwargs.get('message', '-'), kwargs.get('response_code','')),
            })
        return werkzeug.utils.redirect(kwargs['result_url'])

    @http.route(['/pay'], type='http', auth='user', website=True)
    def jetcheckout_payment_page(self, **kwargs):
        values = self.jetcheckout_get_data()
        return request.render('payment_jetcheckout.payment_page', values)

    @http.route(['/payment/card/installments'], type='json', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def jetcheckout_get_installments(self, **kwargs):
        values = self.jetcheckout_get_installment_data(**kwargs)
        if 'error' in values:
            return values
        return {'render': request.env['ir.ui.view']._render_template('payment_jetcheckout.installments', values)}

    @http.route(['/payment/card/installment'], type='json', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def jetcheckout_get_installment(self, **kwargs):
        values = self.jetcheckout_get_installment_data(**kwargs)
        if 'error' in values or 'installments' not in values or not len(values['installments']):
            return values
        values['installment'] = {'installments': values['installments'][0]['installments']}
        return {
            'render': request.env['ir.ui.view']._render_template('payment_jetcheckout.installment', values),
            'card': values['installments'][0]['card_family'],
            'logo': values['installments'][0]['card_family_logo']
        }

    @http.route(['/payment/card/payment'], type='json', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def jetcheckout_payment(self, **kwargs):
        acquirer = self.jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        currency = request.env.company.currency_id
        installment = int(kwargs.get('installment', 1))
        amount = float(kwargs['amount'])
        amount_installment = float(kwargs['amount_installment'])
        if amount_installment > 0 and installment != 1:
            amount = amount_installment
        amount_int = int(amount * 100)

        url = '%s/api/v1/payment/simulation' % acquirer._get_jetcheckout_api_url()
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_jetcheckout_env(),
            "campaign_name": "",
            "amount": amount_int,
            "currency": currency.name,
            "installment_count": kwargs['installment'],
            "card_number": str(kwargs['cardnumber']),
            "expire_month": kwargs['expire_month'],
            "expire_year": "20" + kwargs['expire_year'],
            "is_3d": True,
            "hash_data": base64.b64encode(hashlib.sha256(''.join([acquirer.jetcheckout_api_key, str(kwargs['cardnumber']), str(amount_int), acquirer.jetcheckout_secret_key]).encode('utf-8')).digest()).decode('utf-8'),
            "language": "tr",
        }

        vpos, rate = self.jetcheckout_payment_simulation(url, data)
        if not isinstance(vpos, str):
            return vpos

        order_id = str(uuid.uuid4())
        sale_id = int(kwargs.get('order'))
        invoice_id = int(kwargs.get('invoice'))
        partner = request.env['res.partner'].sudo().browse(self.jetcheckout_get_partner(**kwargs))
        fees = self.jetcheckout_get_fees(acquirer=acquirer, **kwargs)

        if not isinstance(fees, float):
            return fees

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_page_hash','=',request.session.hash),('state','=','draft')], limit=1)
        if not tx:
            sequence_code = 'payment.jetcheckout.transaction'
            name = request.env['ir.sequence'].sudo().next_by_code(sequence_code)
            if not name:
                raise ValidationError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
            tx_vals = {
                'reference': name,
                'amount': amount,
                'fees': fees,
                'currency_id': currency.id,
                'acquirer_id': acquirer.id,
                'partner_id': partner.id,
                'partner_name': partner.name,
                'partner_email': partner.email,
                'partner_phone': partner.mobile or partner.phone,
                'partner_zip': partner.zip,
                'partner_address': partner.street,
                'partner_city': partner.city,
                'partner_state_id': partner.state_id.id,
                'partner_country_id': partner.country_id.id,
                'jetcheckout_ip_address': request.httprequest.remote_addr,
                'jetcheckout_card_name': kwargs['card_holder_name'],
                'jetcheckout_card_number': ''.join([kwargs['cardnumber'][:6], '*'*6, kwargs['cardnumber'][-4:]]),
                'jetcheckout_card_type': kwargs['card_type'].capitalize(),
                'jetcheckout_vpos_name': vpos,
                'jetcheckout_order_id': order_id,
                'jetcheckout_payment_amount': amount,
                'jetcheckout_installment_count': installment,
                'jetcheckout_installment_amount': amount / installment if installment > 0 else amount,
                'jetcheckout_commission_rate': rate,
                'jetcheckout_commission_amount': amount * rate / 100,
            }
            tx_vals.update(self.jetcheckout_tx_vals(**kwargs))
            tx = request.env['payment.transaction'].sudo().create(tx_vals)
        else:
            tx_vals = {
                'acquirer_id': acquirer.id,
                'jetcheckout_ip_address': tx.jetcheckout_ip_address or request.httprequest.remote_addr,
                'jetcheckout_card_name': kwargs['card_holder_name'],
                'jetcheckout_card_number': ''.join([kwargs['cardnumber'][:6], '*'*6, kwargs['cardnumber'][-4:]]),
                'jetcheckout_card_type': kwargs['card_type'].capitalize(),
                'jetcheckout_vpos_name': vpos,
                'jetcheckout_order_id': order_id,
                'jetcheckout_payment_amount': amount,
                'jetcheckout_installment_count': installment,
                'jetcheckout_installment_amount': amount / installment if installment > 0 else amount,
                'jetcheckout_commission_rate': rate,
                'jetcheckout_commission_amount': amount * rate / 100,
            }
            tx_vals.update(self.jetcheckout_tx_vals(**kwargs))
            tx.write(tx_vals)

        if sale_id:
            tx.sale_order_ids = [(4, sale_id)]
            sale_order_id = request.env['sale.order'].sudo().browse(sale_id)
            billing_partner_id = sale_order_id.partner_invoice_id
            shipping_partner_id = sale_order_id.partner_shipping_id
            data.update({
                "customer_basket": [{
                    "id": line.product_id.default_code,
                    "name": line.product_id.name,
                    "description": line.name,
                    "qty": line.product_uom_qty,
                    "amount": line.price_total,
                    "is_physical": line.product_id.type == 'product',
                    "category": line.product_id.categ_id.name,
                } for line in sale_order_id.order_line],
                "billing_address": {
                    "contactName": billing_partner_id.name,
                    "address": "%s %s/%s/%s" % (billing_partner_id.street, billing_partner_id.city, billing_partner_id.state_id and billing_partner_id.state_id.name or '', billing_partner_id.country_id and billing_partner_id.country_id.name or ''),
                    "city": billing_partner_id.state_id and billing_partner_id.state_id.name or "",
                    "country": billing_partner_id.country_id and billing_partner_id.country_id.name or "",
                },
                "shipping_address": {
                    "contactName": shipping_partner_id.name,
                    "address": "%s %s/%s/%s" % (shipping_partner_id.street, shipping_partner_id.city, shipping_partner_id.state_id and shipping_partner_id.state_id.name or '', shipping_partner_id.country_id and shipping_partner_id.country_id.name or ''),
                    "city": shipping_partner_id.state_id and shipping_partner_id.state_id.name or "",
                    "country": shipping_partner_id.country_id and shipping_partner_id.country_id.name or "",
                },
            })
        elif invoice_id:
            tx.invoice_ids = [(4, invoice_id)]
        request.session['__jetcheckout_last_tx_id'] = tx.id

        url = '%s/api/v1/payment' % acquirer._get_jetcheckout_api_url()
        fullname = tx.partner_name.split(' ', 1)
        address = []
        if tx.partner_city:
            address.append(tx.partner_city)
        if tx.partner_state_id:
            address.append(tx.partner_state_id.name)
        if tx.partner_country_id:
            address.append(tx.partner_country_id.name)
        data.update({
            "order_id": order_id,
            "card_holder_name": kwargs['card_holder_name'],
            "cvc": kwargs['cvc'],
            "success_url": "https://%s/payment/card/success" % request.httprequest.host,
            "fail_url": "https://%s/payment/card/fail" % request.httprequest.host,
            "customer":  {
                "name": fullname[0],
                "surname": fullname[-1],
                "email": tx.partner_email,
                "id": str(tx.partner_id.id),
                "identity_number": tx.partner_id.vat,
                "phone": tx.partner_phone,
                "ip_address": tx.jetcheckout_ip_address or request.httprequest.remote_addr,
                "postal_code": tx.partner_zip,
                "company": tx.partner_id.parent_id and tx.partner_id.parent_id.name or "",
                "address": "%s %s" % (tx.partner_address, "/".join(address)),
                "city": tx.partner_state_id and tx.partner_state_id.name or "",
                "country": tx.partner_country_id and tx.partner_country_id.name or "",
            },
        })

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if int(result['response_code']) in (0, 307):
                tx.state = 'pending'
                tx.jetcheckout_transaction_id = result['transaction_id']
                redirect_url = '%s/%s' % (result['redirect_url'], result['transaction_id'])
                return {'redirect_url': redirect_url}
            else:
                tx.state = 'error'
                message = _('%s (Error Code: %s)') % (result['message'], result['response_code'])
                tx.write({
                    'state': 'error',
                    'state_message': message,
                })
                values = {'error': message}
        else:
            tx.state = 'error'
            message = _('%s (Error Code: %s)') % (response.reason, response.status_code)
            tx.write({
                'state': 'error',
                'state_message': message,
            })
            values = {'error': message}
        return values

    @http.route(['/payment/card/success', '/payment/card/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_return(self, **kwargs):
        kwargs['result_url'] = '/payment/card/result'
        return self.jetcheckout_process(**kwargs)

    @http.route('/payment/card/shop', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_shop(self, **kwargs):
        kwargs['result_url'] = '/shop/confirmation'
        return self.jetcheckout_process(**kwargs)

    @http.route('/payment/card/order/<int:order_id>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_order(self, order_id, access_token, **kwargs):
        kwargs['result_url'] = '/my/orders/%s?access_token=%s' % (order_id, access_token)
        return self.jetcheckout_process(**kwargs)

    @http.route('/payment/card/invoice/<int:invoice_id>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_invoice(self, invoice_id, access_token, **kwargs):
        kwargs['result_url'] = '/my/invoices/%s?access_token=%s' % (invoice_id, access_token)
        return self.jetcheckout_process(**kwargs)

    @http.route('/payment/card/subscription/<int:subscription_id>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_subscription(self, subscription_id, access_token, **kwargs):
        kwargs['result_url'] = '/my/subscription/%s/%s' % (subscription_id, access_token)
        return self.jetcheckout_process(**kwargs)

    @http.route(['/payment/card/result'], type='http', auth='public', methods=['GET'], csrf=False, website=True, sitemap=False)
    def jetcheckout_result(self, **kwargs):
        values = self.jetcheckout_get_data()
        last_tx_id = request.session.get('__jetcheckout_last_tx_id')
        values['tx'] = request.env['payment.transaction'].sudo().browse(last_tx_id)
        if last_tx_id:
            del request.session['__jetcheckout_last_tx_id']
        return request.render('payment_jetcheckout.payment_page_result', values)

    @http.route(['/payment/card/terms'], type='json', auth='public', csrf=False, website=True)
    def jetcheckout_terms(self, **kwargs):
        acquirer = self.jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        return acquirer.sudo()._render_jetcheckout_terms(request.env.company.id, self.jetcheckout_get_partner(**kwargs))

    @http.route(['/payment/card/report/<string:name>/<string:order_id>'], type='http', auth='public', methods=['GET'], csrf=False, website=True)
    def jetcheckout_report(self, name, order_id, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',order_id)])
        if not tx:
            return werkzeug.utils.redirect('/404')

        pdf = request.env.ref('payment_jetcheckout.report_%s' % name).with_user(SUPERUSER_ID)._render_qweb_pdf([tx.id])[0]
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/payment/card/transactions', '/payment/card/transactions/page/<int:page>'], type='http', auth='user', website=True)
    def jetcheckout_transactions(self, page=0, tpp=20, **kwargs):
        values = self.jetcheckout_get_data()
        partner = request.env.user.partner_id
        tx_ids = request.env['payment.transaction'].sudo().search([('acquirer_id','=',values['acquirer'].id),('partner_id','in',(partner.id, partner.commercial_partner_id.id))])
        pager = request.website.pager(url='/payment/card/transactions', total=len(tx_ids), page=page, step=tpp, scope=7, url_args=kwargs)
        offset = pager['offset']
        txs = tx_ids[offset: offset + tpp]
        values.update({
            'pager': pager,
            'txs': txs,
            'tpp': tpp,
        })
        return request.render('payment_jetcheckout.payment_page_transaction', values)

    @http.route(['/payment/card/ledger', '/payment/card/ledger/page/<int:page>'], type='http', auth='user', website=True)
    def jetcheckout_ledger(self, page=0, tpp=40, **kwargs):
        values = self.jetcheckout_get_data()
        partner = request.env.user.partner_id
        aml_ids = request.env['account.move.line'].sudo().search([('company_id','=',values['company'].id),('partner_id','in',(partner.id, partner.commercial_partner_id.id)),('account_internal_type','in',('receivable','payable')),('parent_state','=','posted')])
        pager = request.website.pager(url='/payment/card/ledger', total=len(aml_ids), page=page, step=tpp, scope=7, url_args=kwargs)
        offset = pager['offset']
        amls = aml_ids[offset: offset + tpp]
        balance_sum = sum(aml_ids[:offset].mapped('balance'))
        values.update({
            'pager': pager,
            'amls': amls,
            'tpp': tpp,
            'balance_sum': balance_sum,
        })
        return request.render('payment_jetcheckout.payment_page_ledger', values)

    #@http.route(['/payment/card/result'], type='http', auth='public', csrf=False, method=['GET', 'POST'])
    #def jetcheckout_get_result(self, **kwargs):
    #    request.env['payment.transaction'].sudo().form_feedback(kwargs, 'jetcheckout')
    #    return werkzeug.utils.redirect('/payment/process')

    #@http.route(['/payment/card/create'], type='json', auth='public', csrf=False)
    #def jetcheckout_create(self, verify_validity=False, **kwargs):
    #    if not kwargs.get('partner_id'):
    #        kwargs = dict(kwargs, partner_id=request.env.user.partner_id.id)
    #    acquirer = request.env['payment.acquirer'].browse(int(kwargs.get('acquirer_id')))

    #    token = acquirer.s2s_process(kwargs)
    #    if not token:
    #        return {'result': False}

    #    res = {
    #        'result': True,
    #        'id': token.id,
    #        'short_name': token.short_name,
    #        '3d_secure': False,
    #        'verified': False,
    #    }

    #    if verify_validity != False:
    #        token.validate()
    #        res['verified'] = token.verified
    #    return res

    #@http.route('/payment/card/prepare', type='json', auth='public', csrf=False)
    #def jetcheckout_prepare(self, **kwargs):
    #    return request.env['payment.transaction'].sudo().jetcheckout_prepare_transaction(kwargs)
