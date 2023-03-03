# -*- coding: utf-8 -*-
import werkzeug
import json
import requests
import uuid
import base64
import hashlib
import logging

from odoo import fields, http, SUPERUSER_ID, _
from odoo.http import request
from odoo.tools.misc import formatLang, get_lang
from odoo.tools.float_utils import float_compare, float_round
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class JetcheckoutController(http.Controller):

    @staticmethod
    def _jetcheckout_get_acquirer(acquirer=False, providers=None, limit=None):
        if acquirer:
            if isinstance(acquirer, int):
                return request.env['payment.acquirer'].sudo().browse(acquirer)
            else:
                return acquirer

        return request.env['payment.acquirer'].sudo()._get_acquirer(website=request.website, providers=providers, limit=limit)

    @staticmethod
    def _jetcheckout_get_partner(id=None):
        return request.env['res.partner'].sudo().browse(id) if id else request.env.user.partner_id.commercial_partner_id

    @staticmethod
    def _jetcheckout_get_partner_campaign(pid):
        partner = JetcheckoutController._jetcheckout_get_partner(pid)
        return partner.campaign_id.name or ''

    @staticmethod
    def _jetcheckout_get_installment_description(installment):
        if installment['plus_installment'] > 0:
            if installment['plus_installment_description']:
                return '%s + %s (%s)' % (installment['installment_count'], installment['plus_installment'], installment['plus_installment_description'])
            else:
                return '%s + %s' % (installment['installment_count'], installment['plus_installment'])
        return '%s' % installment['installment_count']

    def _jetcheckout_tx_vals(self, **kwargs):
        return {'jetcheckout_payment_ok': kwargs.get('payment_ok', True)}

    @staticmethod
    def _jetcheckout_get_data(acquirer=False, company=False, transaction=False, balance=True):
        acquirer = JetcheckoutController._jetcheckout_get_acquirer(acquirer=acquirer, providers=['jetcheckout'], limit=1)
        company = company or request.env.company
        currency = transaction and transaction.currency_id or company.currency_id
        lang = get_lang(request.env)
        partner = request.env.user.partner_id
        partner_commercial = partner.commercial_partner_id
        partner_contact = partner if partner.parent_id else False
        campaign = transaction.jetcheckout_campaign_name if transaction else partner.campaign_id.name if partner else ''
        card_family = JetcheckoutController._jetcheckout_get_card_family(acquirer=acquirer, campaign=campaign)

        vals = {
            'partner': partner_commercial,
            'contact': partner_contact,
            'acquirer': acquirer,
            'company': company,
            'campaign': campaign,
            'card_family': card_family,
            'no_terms': not acquirer.provider == 'jetcheckout' or acquirer.jetcheckout_no_terms,
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
            balance = partner_commercial.credit - partner_commercial.debit
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

    def _jetcheckout_get_installment_data(self, acquirer=False, **kwargs):
        acquirer = self._jetcheckout_get_acquirer(acquirer=acquirer, providers=['jetcheckout'], limit=1)
        currency = request.env.company.currency_id
        bin_number = kwargs['cardnumber'][:6] if len(kwargs.get('cardnumber', [])) >= 6 else False
        prefix = kwargs.get('prefix', '')
        url = '%s/api/v1/prepayment/%sinstallment_options' % (acquirer._get_jetcheckout_api_url(), prefix)
        pid = 'partner' in kwargs and int(kwargs['partner']) or None
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_jetcheckout_env(),
            "language": "tr",
            "currency": currency.name,
            "campaign_name": kwargs['campaign'] or self._jetcheckout_get_partner_campaign(pid),
        }
        if prefix:
            data.update({"bin": bin_number})

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            if result['response_code'] == "00":
                installments = []
                amount = kwargs.get('amount', 0)
                amount_installment = kwargs.get('amount_installment', 0)
                installment_options = result.get('installment_options', result.get('installments', []))
                for options in installment_options:
                    installment_list = []
                    for installment in options['installments']:
                        installment['installment_desc'] = self._jetcheckout_get_installment_description(installment)
                        if amount_installment > 0 and amount > 0 and installment['installment_count'] != 1:
                            installment['installment_rate'] = (100 * amount_installment / amount) - 100
                        else:
                            installment['installment_rate'] = 0.0
                        installment['total_installment'] = int(installment['installment_count']) + installment['plus_installment']
                        installment_list.append(installment)
                    installment_list.sort(key=lambda x: int(x['installment_count']))
                    installments.append(options)

                values = {
                    'installments': installments,
                    'amount': amount,
                    'currency': currency,
                    's2s_form': kwargs.get('s2s', False)
                }
            elif result['response_code'] == "00104":
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
                            "total_installment": 1,
                            "installment_rate": 0.0,
                            "installment_desc": "1",
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

    @staticmethod
    def _jetcheckout_get_card_family(**kwargs):
        acquirer = JetcheckoutController._jetcheckout_get_acquirer(acquirer=kwargs['acquirer'], providers=['jetcheckout'], limit=1)
        currency = request.env.company.currency_id
        url = '%s/api/v1/prepayment/installment_options' % acquirer._get_jetcheckout_api_url()
        pid = 'partner' in kwargs and int(kwargs['partner']) or None
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_jetcheckout_env(),
            "language": "tr",
            "currency": currency.name,
            "campaign_name": kwargs['campaign'] or JetcheckoutController._jetcheckout_get_partner_campaign(pid),
            "is_3d": True,
        }

        try:
            response = requests.post(url, data=json.dumps(data), timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == "00":
                    installments = result.get('installment_options', [])
                    card_family = set()
                    for installment in installments:
                        card_family.add(installment['card_family_logo'])
                    return list(card_family)
                else:
                    return []
            else:
                return []
        except:
            return []

    def _jetcheckout_get_transaction(self):
        return False

    def _jetcheckout_process(self, **kwargs):
        if 'order_id' not in kwargs:
            return '/404', None, True

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', kwargs.get('order_id'))], limit=1)
        if not tx:
            return '/404', None, True

        url = kwargs.get('result_url', '/payment/card/result')
        tx.with_context(domain=request.httprequest.referrer)._jetcheckout_query()
        return url, tx, False

    @http.route('/payment/card/acquirer', type='json', auth='user', website=True)
    def jetcheckout_payment_acquirer(self):
        acquirer = JetcheckoutController._jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        return {'id': acquirer.id}

    @http.route('/payment/card/type', type='json', auth='user', website=True)
    def jetcheckout_payment_card_type(self, acquirer=False):
        acquirer = JetcheckoutController._jetcheckout_get_acquirer(acquirer=acquirer, providers=['jetcheckout'], limit=1)
        if acquirer:
            return [{'id': icon.id, 'name': icon.name, 'src': icon.image} for icon in acquirer.payment_icon_ids]
        return []

    @http.route('/payment/card/family', type='json', auth='user', website=True)
    def jetcheckout_payment_card_family(self, **kwargs):
        acquirer = JetcheckoutController._jetcheckout_get_acquirer(acquirer=kwargs['acquirer'], providers=['jetcheckout'], limit=1)
        if acquirer:
            return self._jetcheckout_get_card_family(**kwargs)
        return []

    @http.route(['/pay'], type='http', auth='user', website=True)
    def jetcheckout_payment_page(self, **kwargs):
        values = self._jetcheckout_get_data()
        if not values['acquirer'].jetcheckout_payment_page:
            raise werkzeug.exceptions.NotFound()
        return request.render('payment_jetcheckout.payment_page', values)

    @http.route(['/payment/card/installments'], type='json', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def jetcheckout_get_installments(self, **kwargs):
        values = self._jetcheckout_get_installment_data(**kwargs)
        if 'error' in values:
            return values

        if kwargs.get('list'):
            return values

        return {'render': request.env['ir.ui.view']._render_template('payment_jetcheckout.installments', values)}

    @http.route(['/payment/card/installment'], type='json', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def jetcheckout_get_installment(self, **kwargs):
        values = self._jetcheckout_get_installment_data(**kwargs)
        if 'error' in values or 'installments' not in values or not len(values['installments']):
            return values

        installment = values['installments'][0]
        installments = installment['installments']
        request.session['__tx_installments'] = installments
        values['installment'] = {'installments': installments}
        res = {'card': installment['card_family'], 'logo': installment['card_family_logo']}

        if kwargs.get('render'):
            template = kwargs.get('template', 'payment_jetcheckout.installment')
            res.update({'render': request.env['ir.ui.view']._render_template(template, values)})

        if kwargs.get('list'):
            res.update(values['installment'])

        return res

    @http.route(['/payment/card/pay'], type='json', auth='public', csrf=False, sitemap=False, website=True)
    def jetcheckout_payment(self, **kwargs):
        installment_count = int(kwargs.get('installment', 1))
        installments = request.session.get('__tx_installments', [])
        installment = None
        for i in installments:
            if i['installment_count'] == installment_count:
                installment = i
                break
        if not installment:
            raise ValidationError(_('An error occured. Please restart your payment transaction.'))

        amount = float(kwargs.get('amount', 0))
        amount_installment = float(kwargs.get('amount_installment', 0))
        if amount_installment > 0 and installment != 1:
            amount = amount_installment

        installment_count = installment['installment_count'] + installment['plus_installment']
        installment_desc = installment['installment_desc']
        cost_rate = installment['cost_rate']
        customer_rate = installment['customer_rate']
        customer_amount = amount * customer_rate / 100
        amount_total = float_round(amount + customer_amount, 2)
        cost_amount = float_round(amount_total * cost_rate / 100, 2)
        amount_integer = int(amount_total * 100)

        acquirer = self._jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        url = '%s/api/v1/payment/simulation' % acquirer._get_jetcheckout_api_url()
        pid = 'partner' in kwargs and int(kwargs['partner']) or None
        partner = self._jetcheckout_get_partner(pid)
        currency = request.env.company.currency_id
        hash = base64.b64encode(hashlib.sha256(''.join([acquirer.jetcheckout_api_key, str(kwargs['cardnumber']), str(amount_integer), acquirer.jetcheckout_secret_key]).encode('utf-8')).digest()).decode('utf-8')
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_jetcheckout_env(),
            "campaign_name": kwargs['campaign'] or '',
            "amount": amount_integer,
            "currency": currency.name,
            "installment_count": installment_count,
            "card_number": str(kwargs['cardnumber']),
            "expire_month": kwargs['expire_month'],
            "expire_year": "20" + kwargs['expire_year'],
            "is_3d": True,
            "hash_data": hash,
            "language": "tr",
        }

        order_id = str(uuid.uuid4())
        sale_id = int(kwargs.get('order', 0))
        invoice_id = int(kwargs.get('invoice', 0))

        tx = self._jetcheckout_get_transaction()
        vals = {
            'acquirer_id': acquirer.id,
            'callback_hash': hash,
            'jetcheckout_website_id': request.website.id,
            'jetcheckout_ip_address': tx and tx.jetcheckout_ip_address or request.httprequest.remote_addr,
            'jetcheckout_campaign_name': kwargs['campaign'] or False,
            'jetcheckout_card_name': kwargs['card_holder_name'],
            'jetcheckout_card_number': ''.join([kwargs['cardnumber'][:6], '*'*6, kwargs['cardnumber'][-4:]]),
            'jetcheckout_card_type': kwargs['card_type'].capitalize(),
            'jetcheckout_card_family': kwargs['card_family'].capitalize(),
            'jetcheckout_order_id': order_id,
            'jetcheckout_payment_amount': amount,
            'jetcheckout_installment_count': installment_count,
            'jetcheckout_installment_description': installment_desc,
            'jetcheckout_installment_amount': amount / installment_count if installment_count > 0 else amount,
            'jetcheckout_commission_rate': cost_rate,
            'jetcheckout_commission_amount': cost_amount,
            'jetcheckout_customer_rate': customer_rate,
            'jetcheckout_customer_amount': customer_amount,
        }

        if tx:
            vals.update(self._jetcheckout_tx_vals(**kwargs))
            tx.write(vals)
        else:
            sequence_code = 'payment.jetcheckout.transaction'
            name = request.env['ir.sequence'].sudo().next_by_code(sequence_code)
            if not name:
                raise ValidationError(_('You have to define a sequence for %s in your company.') % (sequence_code,))

            vals.update({
                'reference': name,
                'amount': amount_total,
                'fees': cost_amount,
                'currency_id': currency.id,
                'acquirer_id': acquirer.id,
                'partner_id': partner.id,
                'operation': 'online_direct',
            })
            vals.update(self._jetcheckout_tx_vals(**kwargs))
            tx = request.env['payment.transaction'].sudo().create(vals)

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
        request.session['__tx_id'] = tx.id

        url = '%s/api/v1/payment' % acquirer._get_jetcheckout_api_url()
        fullname = tx.partner_name.split(' ', 1)
        address = []
        if tx.partner_city:
            address.append(tx.partner_city)
        if tx.partner_state_id:
            address.append(tx.partner_state_id.name)
        if tx.partner_country_id:
            address.append(tx.partner_country_id.name)
        success_url = '/payment/card/success' if 'success_url' not in kwargs or not kwargs['success_url'] else kwargs['success_url']
        fail_url = '/payment/card/fail' if 'fail_url' not in kwargs or not kwargs['fail_url'] else kwargs['fail_url']
        data.update({
            "order_id": order_id,
            "card_holder_name": kwargs['card_holder_name'],
            "cvc": kwargs['cvc'],
            "success_url": "https://%s%s" % (request.httprequest.host, success_url),
            "fail_url": "https://%s%s" % (request.httprequest.host, fail_url),
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
            if result['response_code'] in ("00", "00307"):
                rurl = result['redirect_url']
                txid = result['transaction_id']
                tx.write({
                    'state': 'pending',
                    'acquirer_reference': txid,
                    'jetcheckout_transaction_id': txid,
                    'last_state_change': fields.Datetime.now(),
                })
                return {'url': '%s/%s' % (rurl, txid), 'id': tx.id}
            else:
                tx.state = 'error'
                message = _('%s (Error Code: %s)') % (result['message'], result['response_code'])
                tx.write({
                    'state': 'error',
                    'state_message': message,
                    'last_state_change': fields.Datetime.now(),
                })
                values = {'error': message}
        else:
            tx.state = 'error'
            message = _('%s (Error Code: %s)') % (response.reason, response.status_code)
            tx.write({
                'state': 'error',
                'state_message': message,
                'last_state_change': fields.Datetime.now(),
            })
            values = {'error': message}
        return values

    @http.route(['/payment/card/success', '/payment/card/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_return(self, **kwargs):
        _logger.error(kwargs)
        kwargs['result_url'] = '/payment/card/result'
        url, tx, status = self._jetcheckout_process(**kwargs)
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/shop', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_shop(self, **kwargs):
        kwargs['result_url'] = '/shop/confirmation'
        url, tx, status = self._jetcheckout_process(**kwargs)
        if request.session.get('__tx_id'):
            del request.session['__tx_id']
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/order/<int:order>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_order(self, order, access_token, **kwargs):
        kwargs['result_url'] = '/my/orders/%s?access_token=%s' % (order, access_token)
        url, tx, status = self._jetcheckout_process(**kwargs)
        if request.session.get('__tx_id'):
            del request.session['__tx_id']
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/invoice/<int:invoice>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_invoice(self, invoice, access_token, **kwargs):
        kwargs['result_url'] = '/my/invoices/%s?access_token=%s' % (invoice, access_token)
        url, tx, status = self._jetcheckout_process(**kwargs)
        if request.session.get('__tx_id'):
            del request.session['__tx_id']
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/subscription/<int:subscription>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_subscription(self, subscription, access_token, **kwargs):
        kwargs['result_url'] = '/my/subscription/%s/%s' % (subscription, access_token)
        url, tx, status = self._jetcheckout_process(**kwargs)
        if request.session.get('__tx_id'):
            del request.session['__tx_id']
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/custom/<int:record>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def jetcheckout_custom(self, record, access_token, **kwargs):
        kwargs['result_url'] = '/payment/confirmation'
        url, tx, status = self._jetcheckout_process(**kwargs)
        url += '?tx_id=%s&access_token=%s' % (tx.id, access_token)
        if request.session.get('__tx_id'):
            del request.session['__tx_id']
        return werkzeug.utils.redirect(url)

    @http.route(['/payment/card/result'], type='http', auth='public', methods=['GET'], csrf=False, website=True, sitemap=False)
    def jetcheckout_result(self, **kwargs):
        values = self._jetcheckout_get_data()
        last_tx_id = request.session.get('__tx_id')
        values['tx'] = request.env['payment.transaction'].sudo().browse(last_tx_id)
        if last_tx_id:
            del request.session['__tx_id']
        return request.render('payment_jetcheckout.payment_page_result', values)

    @http.route(['/payment/card/terms'], type='json', auth='public', csrf=False, website=True)
    def jetcheckout_terms(self, **kwargs):
        acquirer = self._jetcheckout_get_acquirer(providers=['jetcheckout'], limit=1)
        domain = request.httprequest.referrer
        pid = 'partner' in kwargs and int(kwargs['partner']) or None
        partner = self._jetcheckout_get_partner(pid)
        return acquirer.sudo().with_context(domain=domain)._render_jetcheckout_terms(request.env.company.id, partner.id)

    @http.route(['/payment/card/report/<string:name>/<string:order_id>'], type='http', auth='public', methods=['GET'], csrf=False, website=True)
    def jetcheckout_report(self, name, order_id, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id','=',order_id)], limit=1)
        if not tx:
            raise werkzeug.exceptions.NotFound()

        #pdf = request.env.ref('payment_jetcheckout.report_%s' % name).with_user(SUPERUSER_ID)._render_qweb_pdf([tx.id])[0]
        #pdfhttpheaders = [
        #    ('Content-Type', 'application/pdf'),
        #    ('Content-Length', len(pdf)),
        #]
        #return request.make_response(pdf, headers=pdfhttpheaders)
        html = request.env.ref('payment_jetcheckout.report_%s' % name).with_user(SUPERUSER_ID)._render_qweb_html([tx.id])[0]
        return request.make_response(html)

    @http.route(['/payment/card/transactions', '/payment/card/transactions/page/<int:page>'], type='http', auth='user', website=True)
    def jetcheckout_transactions(self, page=0, tpp=20, **kwargs):
        values = self._jetcheckout_get_data()
        tx_ids = request.env['payment.transaction'].sudo().search([
            ('acquirer_id', '=', values['acquirer'].id),
            ('partner_id', '=', values['partner'].id)
        ])
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
        values = self._jetcheckout_get_data()
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
