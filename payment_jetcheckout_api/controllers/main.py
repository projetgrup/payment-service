# -*- coding: utf-8 -*-
import re
import uuid
import json
import werkzeug
import requests
from werkzeug.exceptions import NotFound
from urllib.parse import unquote

from odoo import fields, http, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.addons.payment_jetcheckout.controllers.main import PayloxController as Controller


class PayloxApiController(Controller):

    def _confirm_bank_webhook(self, tx):
        try:
            url = tx.jetcheckout_api_bank_webhook_url
            data = {'id': tx.jetcheckout_api_id}
            response = requests.post(url, data=data)
            if response.status_code == 200:
                tx.write({
                    'state': 'pending',
                    'last_state_change': fields.Datetime.now(),
                })
            else:
                raise ValidationError('%s (Error Code: %s)' % (response.reason, response.status_code))
        except Exception as e:
            raise ValidationError(e)
        except:
            raise ValidationError('%s (Error Code: %s)' % ('Server Error', '-1'))

    def _set_hash(self, raise_exception=True, **kwargs):
        if '' in kwargs:
            hash = unquote(kwargs[''])
            self._set('hash', hash)
        elif 'hash' in kwargs:
            hash = unquote(kwargs['hash'])
            self._set('hash', hash)
        else:
            hash = self._get('hash')
            if not hash:
                if raise_exception:
                    raise NotFound()
                return False
        return hash

    def _get_transaction(self):
        tx = super()._get_transaction()
        if not tx:
            hash = self._get('hash')
            if not hash:
                return False

            tx = request.env['payment.transaction'].sudo().search([
                ('jetcheckout_api_hash', '!=', False),
                ('jetcheckout_api_hash', '=', hash),
                ('state', 'in', ('draft', 'pending', 'error'))
            ], limit=1)
            if not tx:
                raise ValidationError(_('An error occured. Please restart your payment transaction.'))
        return tx

    def _prepare(self, transaction=None, partner=None, **kwargs):
        values = super()._prepare(transaction=transaction, partner=partner, **kwargs)
        if transaction and transaction.jetcheckout_api_ok:
            values.update({
                'partner_name': transaction.partner_name,
        })
        return values

    def _process(self, **kwargs):
        url, tx, status = super()._process(**kwargs)
        if kwargs.get('skip_url'):
            return url, tx, status

        if not status and tx.jetcheckout_api_hash:
            self._del('hash')

            method = fields.first(tx.paylox_api_method_ids.filtered(lambda m: m.type == 'virtualpos'))
            if method and method.redirect_url:
                status = True
                url = '%s/%s' % (method.redirect_url, tx.jetcheckout_order_id)

        return url, tx, status

    def _get_template(self, path, values):
        method = ''
        if values.get('method'):
            method = f'_{values["method"]["type"]}'
        return 'payment_jetcheckout_api.page_payment%s' % method

    @http.route(['/api/payment/success'], type='http', methods=['GET', 'POST'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_payment_success(self, **kwargs):
        if request.httprequest.method == 'POST':
            kwargs['skip_url'] = True
            url, tx, status = self._process(**kwargs)
            if not tx.jetcheckout_api_success_url:
                raise NotFound()
        else:
            if '' not in kwargs:
                raise NotFound()
            txid = re.split(r'\?|%3F', kwargs[''])[0]
            tx = request.env['payment.transaction'].sudo().paylox_get_transaction(txid)
            if not tx:
                raise NotFound()
        return request.render('payment_jetcheckout_api.page_api_payment_success', {'tx': tx, 'data': json.loads(tx.jetcheckout_data)})

    @http.route(['/api/payment/fail'], type='http', methods=['GET', 'POST'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_payment_fail(self, **kwargs):
        if request.httprequest.method == 'POST':
            kwargs['skip_url'] = True
            url, tx, status = self._process(**kwargs)
            if not tx.jetcheckout_api_fail_url:
                raise NotFound()
        else:
            if '' not in kwargs:
                raise NotFound()
            txid = re.split(r'\?|%3F', kwargs[''])[0]
            tx = request.env['payment.transaction'].sudo().paylox_get_transaction(txid)
            if not tx:
                raise NotFound()
        return request.render('payment_jetcheckout_api.page_api_payment_fail', {'tx': tx, 'data': json.loads(tx.jetcheckout_data)})

    @http.route(['/payment'], type='http', methods=['GET', 'POST'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api(self, **kwargs):
        #self._del() #TODO remove it if unnecessary

        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
            #('state', 'in', ('draft', 'cancel', 'expired'))
        ], limit=1)
        if not tx:
            raise NotFound()
 
        company = tx.company_id or request.env.company
        if company.id != request.website.company_id.id:
            return self._redirect(company_id=company.id)

        self._set('company', tx.company_id.id) #TODO Its acquirer bound has been released
        self._set('token', tx.jetcheckout_order_id)

        if len(tx.paylox_api_method_ids) == 1:
            return werkzeug.utils.redirect('/payment/%s' % fields.first(tx.paylox_api_method_ids).name)

        acquirers = Controller._get_acquirer()
        order = request.env['payment.transaction'].sudo().search([
            ('state', '=', 'pending'),
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '!=', hash),
            ('jetcheckout_api_order', '=', tx.jetcheckout_api_order)
        ], limit=1)
        values = {
            'acquirers': acquirers,
            'company': company,
            'tx': tx,
            'order': order,
            'system': 'jetcheckout_api'
        }
        template = self._get_template('/payment', values)
        return request.render(template, values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/card'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_card(self, **kwargs):
        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
            #('state', 'in', ('draft', 'cancel', 'expired'))
        ], limit=1)
        if not tx:
            raise NotFound()

        method = tx.paylox_api_method_ids.filtered(lambda m: m.type == 'virtualpos')
        if not method:
            raise NotFound()

        acquirer = request.env['payment.acquirer']._get_acquirer(
            company=tx.company_id,
            website=request.website,
            providers=['jetcheckout'],
            limit=1,
        )
        values = self._prepare(acquirer=acquirer, company=tx.company_id, partner=tx.partner_id, transaction=tx, balance=False, filters={'type': ['virtualpos']})
        values.update({'tx': tx, 'method': method})
        template = self._get_template('/payment/card', values)
        return request.render(template, values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/pos'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_pos(self, **kwargs):
        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
            #('state', 'in', ('draft', 'cancel', 'expired'))
        ], limit=1)
        if not tx:
            raise NotFound()
        
        method = tx.paylox_api_method_ids.filtered(lambda m: m.type == 'physicalpos')
        if not method:
            raise NotFound()

        acquirer = tx.acquirer_id
        values = self._prepare(acquirer=acquirer, company=tx.company_id, partner=tx.partner_id, transaction=tx, balance=False, filters={'type': ['physicalpos']})
        values.update({'tx': tx, 'method': method})
        template = self._get_template('/payment/pos', values)

        url = acquirer._get_paylox_api_url()
        apikey = acquirer.jetcheckout_api_key
        base_url = acquirer.get_base_url()
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        payload = {
            'application_key': apikey,
            'order_id': tx.jetcheckout_order_id,
            'amount': int(tx.amount*100),
            'currency': tx.company_id.currency_id.name,
            'store_code': tx.company_id.payment_method_physical_pos_store_code or '',
            'callback_api_url': '%s/payment/callback' % base_url,
            'mode': acquirer._get_paylox_env(),
            #'document_type': 4,
        }
        if tx.jetcheckout_installment_count and tx.jetcheckout_installment_count > 1:
            payload.update({'installment_count': str(tx.jetcheckout_installment_count)})
        if tx.paylox_product_ids:
            precision = request.env['decimal.precision'].sudo().precision_get('Product Price')
            payload.update({
                'sale_items': [{
                    'name': product.name or '',
                    'barcode': product.code or '',
                    'qty': round(product.qty, precision),
                    'price': round(product.price, precision),
                    'amount': round(product.qty*product.price, precision),
                    'tax_rate': 20
                } for product in tx.paylox_product_ids]
            })

        devices = method.type_physicalpos_ids
        device_ids = []
        device_owner = ''
        device_name = ''
        if devices:        
            device_owner = devices[0].type
            if device_owner == 'pavo':
                device_name = devices[0].name
                device_ids.append(device_name)
            else:
                device_name = devices[0].name
                device_ids.extend(devices.mapped('name'))

        if device_ids:
            payload.update({'device_ids': device_ids})

        if device_owner:
            payload.update({'device_owner': device_owner})

        request_count = 0
        def init_physical_payment():
            nonlocal request_count
            if request_count == 5:
                message = _('Request cycle exceeded. Please contact with system administrator.')
                tx.write({
                    'state': 'error',
                    'state_message': message,
                    'last_state_change': fields.Datetime.now(),
                })
                values.update({'error': message})
                return

            request_count += 1
            response = requests.post('%s/api/v1/physical/payment' % url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == '00158':
                    response = requests.post('%s/api/v1/physical/pairing' % url, json={
                        "application_key": apikey,
                        "device_id": device_name,
                        "device_owner": device_owner
                    })
                    if response.status_code == 200:
                        result = response.json()
                        if result['pairing_code']:
                            values.update({'method_physical_code': result['pairing_code']})
                        else:
                            message = _('%s - (Error Code: %s)') % (result['message'], result['response_code'])
                            tx.write({
                                'state': 'error',
                                'state_message': message,
                                'last_state_change': fields.Datetime.now(),
                            })
                            values.update({'error': message})
                    else:
                        message = _('%s - (Error Code: %s)') % (response.reason, response.status_code)
                        tx.write({
                            'state': 'error',
                            'state_message': message,
                            'last_state_change': fields.Datetime.now(),
                        })
                        values.update({'error': message})

                elif result['response_code'] == '00202':
                    tx.write({
                        'state': 'pending', 
                        'last_state_change': fields.Datetime.now(),
                        'jetcheckout_payment_type': 'physicalpos',
                        'jetcheckout_transaction_id': result['transaction_id']
                    })
                    values.update({'name': result['pos_order_number']})

                elif result['response_code'] == '00122':
                    order_aux_id = 'x%s' % str(uuid.uuid4())
                    tx.write({'jetcheckout_order_aux_id': order_aux_id})
                    payload.update({"order_id": order_aux_id})
                    init_physical_payment()

                else:
                    message = _('%s - (Error Code: %s)') % (result['message'], result['response_code'])
                    tx.write({
                        'state': 'error',
                        'state_message': message,
                        'last_state_change': fields.Datetime.now(),
                    })
                    values.update({'error': message})

            else:
                message = _('%s - (Error Code: %s)') % (response.reason, response.status_code)
                tx.write({
                    'state': 'error',
                    'state_message': message,
                    'last_state_change': fields.Datetime.now(),
                })
                values.update({'error': message})

        init_physical_payment()
        return request.render(template, values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/bank'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_bank(self, **kwargs):
        hash = self._set_hash(**kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('state', '=', 'draft'),
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
        ], limit=1)
        if not tx:
            raise NotFound()
        elif 'transfer' not in tx.paylox_api_method_ids.mapped('type'):
            raise NotFound()

        order = request.env['payment.transaction'].sudo().search([
            ('state', '=', 'pending'),
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '!=', hash),
            ('jetcheckout_api_order', '=', tx.jetcheckout_api_order),
        ], limit=1)
        if order:
            self._confirm_bank_webhook(tx)
            return werkzeug.utils.redirect('/payment/bank/result')

        acquirer = request.env['payment.acquirer']._get_acquirer(
            company=tx.company_id,
            website=request.website,
            providers=['transfer'],
            limit=1,
        )
        values = self._prepare(
            acquirer=acquirer,
            company=tx.company_id,
            balance=False,
            filters={'type': ['bank']}
        )
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.payment_bank_page', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/transfer'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_transfer(self, **kwargs):
        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
            #('state', 'in', ('draft', 'cancel', 'expired'))
        ], limit=1)
        if not tx:
            raise NotFound()
        elif 'transfer' not in tx.paylox_api_method_ids.mapped('type'):
            raise NotFound()

        acquirer = request.env['payment.acquirer']._get_acquirer(
            company=tx.company_id,
            website=request.website,
            providers=['jetcheckout'],
            limit=1,
        )
        values = self._prepare(
            acquirer=acquirer,
            company=tx.company_id,
            balance=False,
        )
        values = self._prepare(acquirer=acquirer, company=tx.company_id, transaction=tx, balance=False, filters={'type': ['transfer']})
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.page_transfer', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/wallet'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_wallet(self, **kwargs):
        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
            #('state', 'in', ('draft', 'cancel', 'expired'))
        ], limit=1)
        if not tx:
            raise NotFound()
        elif 'wallet' not in tx.paylox_api_method_ids.mapped('type'):
            raise NotFound()

        acquirer = request.env['payment.acquirer']._get_acquirer(
            company=tx.company_id,
            website=request.website,
            providers=['jetcheckout'],
            limit=1,
        )
        values = self._prepare(
            acquirer=acquirer,
            company=tx.company_id,
            balance=False,
        )
        values = self._prepare(acquirer=acquirer, company=tx.company_id, transaction=tx, balance=False, filters={'type': ['wallet']})
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.page_wallet', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/credit'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_credit(self, **kwargs):
        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
            #('state', 'in', ('draft', 'cancel', 'expired'))
        ], limit=1)
        if not tx:
            raise NotFound()
        elif 'credit' not in tx.paylox_api_method_ids.mapped('type'):
            raise NotFound()

        acquirer = request.env['payment.acquirer']._get_acquirer(
            company=tx.company_id,
            website=request.website,
            providers=['jetcheckout'],
            limit=1,
        )
        values = self._prepare(
            acquirer=acquirer,
            company=tx.company_id,
            balance=False,
        )
        values = self._prepare(acquirer=acquirer, company=tx.company_id, transaction=tx, balance=False, filters={'type': ['credit']})
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.page_credit', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/bank/result'], type='http', methods=['GET'], auth='public', csrf=False, sitemap=False, website=True)
    def page_api_bank_result(self, **kwargs):
        hash = self._set_hash(**kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('state', '=', 'pending'),
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
        ], limit=1)
        if not tx:
            raise NotFound()
        elif 'transfer' not in tx.paylox_api_method_ids.mapped('type'):
            raise NotFound()

        acquirer = request.env['payment.acquirer']._get_acquirer(
            company=tx.company_id,
            website=request.website,
            providers=['transfer'],
            limit=1,
        )
        values = self._prepare(
            acquirer=acquirer,
            company=tx.company_id,
            balance=False
        )
        values.update({'tx': tx})
        return request.render('payment_jetcheckout_api.payment_bank_page', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @http.route(['/payment/bank/confirm'], type='json', auth='public')
    def page_api_confirm(self, **kwargs):
        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('state', '=', 'draft'),
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash),
        ], limit=1)
        if not tx:
            return '/404'
        elif 'transfer' not in tx.paylox_api_method_ids.mapped('type'):
            return '/404'

        self._confirm_bank_webhook(tx)
        return '/payment/bank/result'

    @http.route(['/payment/bank/return'], type='json', auth='public')
    def page_api_return(self, **kwargs):
        hash = self._set_hash(raise_exception=False, **kwargs)
        tx = request.env['payment.transaction'].sudo().search([
            ('jetcheckout_api_hash', '!=', False),
            ('jetcheckout_api_hash', '=', hash)
        ], limit=1)
        if not tx:
            return '/404'
        elif 'transfer' not in tx.paylox_api_method_ids.mapped('type'):
            return '/404'

        self._del()
        return tx.jetcheckout_api_bank_return_url
