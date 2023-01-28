# -*- coding: utf-8 -*-
# Copyright © 2022 Projetgrup (https://www.bulutkobi.io)
# Part of Projetgrup BulutKOBI. See LICENSE file for full copyright and licensing details.

import json
import uuid
import requests
import base64
import hashlib
from datetime import datetime
from dateutil.relativedelta import relativedelta
from urllib.parse import quote, unquote
from werkzeug.exceptions import NotFound
from werkzeug.utils import redirect

from odoo import fields
from odoo.tools.translate import _
from odoo.http import request, route
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
from odoo.addons.payment_jetcheckout.controllers.main import JetcheckoutController as JetController


import logging
_logger = logging.getLogger(__name__)


class JetControllerPos(JetController):

    def _pos_link_cancel(self, tx):
        if not tx:
            return

        tx._jetcheckout_cancel()

        try:
            url = tx.pos_method_id.jetcheckout_link_url
            requests.put('%s/api/v1/payment/cancel' % url, json={
                'apikey': tx.pos_method_id.jetcheckout_link_apikey,
                'hash': tx.callback_hash
            }, timeout=10)
        except:
            pass

    def _pos_link_expire(self, tx, force=False):
        if not tx:
            return

        if not force and not tx.jetcheckout_date_expiration < datetime.now():
            return

        tx._jetcheckout_expire()

        try:
            url = tx.pos_method_id.jetcheckout_link_url
            requests.put('%s/api/v1/payment/expire' % url, json={
                'apikey': tx.pos_method_id.jetcheckout_link_apikey,
                'hash': tx.callback_hash
            }, timeout=10)
        except:
            pass

    def _pos_physical_cancel(self, tx):
        if not tx:
            return

        tx._jetcheckout_cancel()

    @route(['/pos/card/success', '/pos/card/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def pos_card_preresult(self, **kwargs):
        self._jetcheckout_process(**kwargs)
        return redirect('/pos/card/result?=%s' % kwargs.get('order_id'))

    @route(['/pos/card/result'], type='http', auth='public', methods=['GET'], csrf=False, website=True, sitemap=False)
    def pos_card_result(self, **kwargs):
        if '' not in kwargs:
            raise NotFound()

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', kwargs[''])], limit=1)
        if not tx:
            raise NotFound()

        if '__tx_id' in request.session:
            del request.session['__tx_id']

        return request.render('pos_jetcheckout.payment_result', {
            'result': json.dumps({
                'id': tx.id,
                'state': tx.state,
                'message': tx.state_message.replace('"', '\\"').replace('\n', ' ')
            })
        })

    @route(['/pos/link/redirect'], type='http', auth='public', methods=['GET'], csrf=False, website=True, sitemap=False)
    def pos_link_redirect(self, **kwargs):
        if '' not in kwargs:
            raise NotFound()

        hash = unquote(kwargs[''])
        tx = request.env['payment.transaction'].sudo().search([
            ('state', 'in', ('pending', 'cancel', 'expired')),
            ('callback_hash', '=', hash)
        ], limit=1)
        if not tx:
            raise NotFound()

        self._pos_link_expire(tx)
        url = tx.pos_method_id.jetcheckout_link_url
        return redirect('%s/payment/card?=%s' % (url, quote(hash, safe='')))

    @route(['/pos/link/prepare'], type='json', auth='user')
    def pos_link_prepare(self, **kwargs):
        if not kwargs['amount'] > 0:
            return {'error': _('Amount must be greater than zero')}

        method = request.env['pos.payment.method'].sudo().browse(kwargs.get('method', 0))
        if not method:
            return {'error': _('Method not found')}

        partner = request.env['res.partner'].sudo().browse(kwargs.get('partner', 0))
        if not partner:
            return {'error': _('Partner not found')}

        sequence = 'payment.jetcheckout.transaction'
        name = request.env['ir.sequence'].sudo().next_by_code(sequence)
        if not name:
            return {'error': _('You have to define a sequence for %s') % (sequence,)}

        company = request.env.company
        order = kwargs.get('order', {})
        duration = kwargs.get('duration', 0)
        date_expiration = datetime.now() + relativedelta(seconds=duration)
        tx = request.env['payment.transaction'].sudo().create({
            'reference': name,
            'acquirer_id': kwargs['acquirer'],
            'amount': kwargs['amount'],
            'partner_id': partner.id,
            'company_id': company.id,
            'currency_id': company.currency_id.id,
            'pos_method_id': method.id,
            'pos_order_name': order.get('name', ''),
            'state': 'draft',
            'jetcheckout_api_ok': True,
            'jetcheckout_date_expiration': date_expiration,
        })

        try:
            url = method.jetcheckout_link_url
            base_url = method._set_url(request.httprequest.host_url)

            apikey = method.jetcheckout_link_apikey
            secretkey = method.jetcheckout_link_secretkey
            hash = base64.b64encode(hashlib.sha256(''.join([apikey, secretkey, str(tx.id)]).encode('utf-8')).digest()).decode('utf-8')

            response = requests.post('%s/api/v1/payment/prepare' % url, json={
                'id': tx.id,
                'apikey': apikey,
                'hash': hash,
                'expiration': date_expiration.isoformat(),
                'partner': {
                    'name': tx.partner_name or '',
                    'vat': tx.partner_vat or '',
                    'email': tx.partner_email or '',
                    'phone': tx.partner_phone or '',
                    'country': tx.partner_country_id and tx.partner_country_id.code or '',
                    'state': tx.partner_state_id and tx.partner_state_id.code or '',
                    'address': tx.partner_address or '',
                    'zip': tx.partner_zip or '',
                    'ip_address': request.httprequest.remote_addr,
                },
                'order': {
                    'name': order.get('name', ''),
                },
                'url': {
                    'card': {
                        'result': '%s/pos/link/result?=%s' % (base_url, quote(hash, safe='')),
                    }
                },
                'amount': kwargs.get('amount', 0),
                'methods': ['card'],
            })
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 0:
                    tx.write({
                        'state': 'pending', 
                        'last_state_change': fields.Datetime.now(),
                        'callback_hash': result['hash']
                    })
                    link = request.env['link.tracker'].sudo().search_or_create({
                        'url': '%s/pos/link/redirect?=%s' % (base_url, quote(hash, safe='')),
                        'title': partner.name
                    })
                    return {
                        'id': tx.id,
                        'url': link.short_url,
                        'email': partner.email or '',
                        'phone': partner.mobile or '',
                        'duration': duration,
                    }
                else:
                    message = _('%s - (Error Code: %s)') % (result['message'], result['status'])
                    tx.write({
                        'state': 'error',
                        'state_message': message,
                        'last_state_change': fields.Datetime.now(),
                    })
                    return {'error': message}
            else:
                message = _('%s - (Error Code: %s)') % (response.reason, response.status_code)
                tx.write({
                    'state': 'error',
                    'state_message': message,
                    'last_state_change': fields.Datetime.now(),
                })
                return {'error': message}
        except Exception as e:
            message = _('%s - (Error Code: -2)') % e
            tx.write({
                'state': 'error',
                'state_message': message,
                'last_state_change': fields.Datetime.now(),
            })
            return {'error': message}

    @route(['/pos/link/cancel'], type='json', auth='user')
    def pos_link_cancel(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().browse(kwargs['id'])
        self._pos_link_cancel(tx)
        return {'status': 0}

    @route(['/pos/link/expire'], type='json', auth='user')
    def pos_link_expire(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().browse(kwargs['id'])
        self._pos_link_expire(tx, force=True)
        return {'status': 0}

    @route(['/pos/link/query'], type='json', auth='user')
    def pos_link_query(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().browse(kwargs['id'])
        if tx:
            if tx.state == 'done':
                return {'status': 0, 'id': tx.id}
            elif tx.state != 'pending':
                return {'status': -1, 'message': tx.state_message}
            return {'status': 1}
        return {'status': -1, 'message': _('Transaction not found')}

    @route(['/pos/link/sms'], type='json', auth='user')
    def pos_link_sms(self, **kwargs):
        if not kwargs['phone']:
            raise ValidationError(_('Please fill phone number'))

        currency = request.env['res.currency'].sudo().browse(kwargs['currency'])
        template = request.env.ref('pos_jetcheckout.sms_template_payment')
        amount = formatLang(request.env, kwargs['amount'])
        context = {
            'amount': amount,
            'currency': currency.name,
            'phone': kwargs['phone'],
            'url': kwargs['url'],
        }
        template.with_context(context).send_sms(kwargs['partner'], {'phone': kwargs['phone']})
        return _('SMS has been sent successfully')

    @route(['/pos/link/email'], type='json', auth='user')
    def pos_link_email(self, **kwargs):
        if not kwargs['email']:
            raise ValidationError(_('Please fill email address'))

        currency = request.env['res.currency'].sudo().browse(kwargs['currency'])
        template = request.env.ref('pos_jetcheckout.mail_template_payment')
        context = {
            'amount': kwargs['amount'],
            'currency': currency,
            'email': kwargs['email'],
            'url': kwargs['url'],
            'company': request.env.company,
            'user': request.env.user.partner_id
        }
        template.with_context(context).send_mail(kwargs['partner'], force_send=True, email_values={'is_notification': True})
        return _('Email has been sent successfully')

    @route(['/pos/link/result'], type='http', auth='public', methods=['GET'], csrf=False, website=True, sitemap=False)
    def pos_link_result(self, **kwargs):
        if '' not in kwargs:
            raise NotFound()

        hash = unquote(kwargs[''])
        tx = request.env['payment.transaction'].sudo().search([
            ('state', '=', 'pending'),
            ('callback_hash', '=', hash)
        ], limit=1)
        if not tx:
            raise NotFound()

        method = tx.pos_method_id
        if not method:
            raise NotFound()

        url = method.jetcheckout_link_url
        try:
            response = requests.get('%s/api/v1/payment/result' % url, json={
                'apikey': method.jetcheckout_link_apikey,
                'hash': hash
            })
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 0:
                    res = result['transaction']
                    tx.write({
                        'state': res['state'],
                        'state_message': res['message'],
                        'last_state_change': fields.Datetime.now(),
                        'fees': res['amounts']['fees'],
                        'jetcheckout_vpos_name': res['virtual_pos_name'],
                        'jetcheckout_order_id': res['order_id'],
                        'jetcheckout_transaction_id': res['transaction_id'],
                        'jetcheckout_ip_address': res['partner']['ip_address'],
                        'jetcheckout_card_name': res['card']['name'],
                        'jetcheckout_card_number': res['card']['number'],
                        'jetcheckout_card_type': res['card']['type'],
                        'jetcheckout_card_family': res['card']['family'],
                        'jetcheckout_payment_amount': res['amounts']['amount'],
                        'jetcheckout_installment_amount': res['amounts']['installment']['amount'],
                        'jetcheckout_installment_description': res['amounts']['installment']['description'],
                        'jetcheckout_installment_count': res['amounts']['installment']['count'],
                        'jetcheckout_commission_rate': res['amounts']['commission']['cost']['rate'],
                        'jetcheckout_commission_amount': res['amounts']['commission']['cost']['amount'],
                        'jetcheckout_customer_rate': res['amounts']['commission']['customer']['rate'],
                        'jetcheckout_customer_amount': res['amounts']['commission']['customer']['amount'],
                    })

                    if res['state'] == 'done':
                        txs = request.env['payment.transaction'].sudo().search([
                            ('id', '!=', tx.id),
                            ('pos_order_name', '=', tx.pos_order_name),
                            ('state', 'in', ('draft', 'pending'))
                        ])
                        txs.write({
                            'state': 'cancel',
                            'last_state_change': fields.Datetime.now(),
                        })
                        tx._jetcheckout_done_postprocess()
                else:
                    tx.write({
                        'state_message': _('%s (Error Code: %s)') % (json.dumps(result, indent=4, default=str), '-1'),
                    })
            else:
                tx.write({
                    'state_message': _('%s (Error Code: %s)') % (response.reason, response.status_code),
                })
        except Exception as e:
            tx.write({
                'state_message': _('%s (Error Code: %s)') % (e, '-1'),
            })
        except:
            tx.write({
                'state_message': _('%s (Error Code: %s)') % ('Server Error', '-1'),
            })

        request.session['__tx_id'] = tx.id
        return redirect('/payment/card/result')

    @route(['/pos/physical/prepare'], type='json', auth='user')
    def pos_physical_prepare(self, **kwargs):
        if not kwargs['amount'] > 0:
            return {'error': _('Amount must be greater than zero')}

        method = request.env['pos.payment.method'].sudo().browse(kwargs.get('method', 0))
        if not method:
            return {'error': _('Method not found')}

        partner = request.env['res.partner'].sudo().browse(kwargs.get('partner', 0))
        if not partner:
            return {'error': _('Partner not found')}

        acquirer = request.env['payment.acquirer'].sudo().browse(kwargs.get('acquirer', 0))
        if not acquirer:
            return {'error': _('Acquirer not found')}

        config = request.env['pos.config'].sudo().browse(kwargs.get('config', 0))
        if not config:
            return {'error': _('Config not found')}

        sequence = 'payment.jetcheckout.transaction'
        name = request.env['ir.sequence'].sudo().next_by_code(sequence)
        if not name:
            return {'error': _('You have to define a sequence for %s') % (sequence,)}

        company = request.env.company
        token = str(uuid.uuid4())
        order = kwargs.get('order', {})
        lines = order.get('lines', {})
        tx = request.env['payment.transaction'].sudo().create({
            'reference': name,
            'acquirer_id': acquirer.id,
            'amount': kwargs['amount'],
            'partner_id': partner.id,
            'company_id': company.id,
            'currency_id': company.currency_id.id,
            'pos_method_id': method.id,
            'pos_order_name': order.get('name', ''),
            'state': 'pending', 
            'state': 'draft', 
            'jetcheckout_order_id': token
        })

        try:
            url = acquirer.jetcheckout_gateway_api
            apikey = acquirer.jetcheckout_api_key
            base_url = method._set_url(request.httprequest.host_url)
            payload = {
                'application_key': apikey,
                'order_id': token,
                'amount': int(kwargs['amount'] * 100),
                'currency': company.currency_id.name,
                'store_code': config.jetcheckout_branch_code,
                'callback_api_url': '%s/pos/physical/result' % base_url,
                'mode': acquirer._get_jetcheckout_env(),
            }

            if lines:
                precision = request.env['decimal.precision'].sudo().precision_get('Product Price')
                payload.update({
                    'sale_items': [{
                        'name': line['name'],
                        'barcode': line['barcode'] or '',
                        'qty': round(line['quantity'], precision),
                        'price': round(line['price'], precision),
                        'amount': round(line['amount'], precision),
                        'tax_rate':  line['tax']
                    } for line in lines]
                })

            response = requests.post('%s/api/v1/physical/payment' % url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == '00202':
                    tx.write({
                        'state': 'pending', 
                        'last_state_change': fields.Datetime.now(),
                        'jetcheckout_transaction_id': result['transaction_id']
                    })
                    return {'id': tx.id}
                else:
                    message = _('%s - (Error Code: %s)') % (result['message'], result['response_code'])
                    tx.write({
                        'state': 'error',
                        'state_message': message,
                        'last_state_change': fields.Datetime.now(),
                    })
                    return {'error': message}
            else:
                message = _('%s - (Error Code: %s)') % (response.reason, response.status_code)
                tx.write({
                    'state': 'error',
                    'state_message': message,
                    'last_state_change': fields.Datetime.now(),
                })
                return {'error': message}
        except Exception as e:
            message = _('%s - (Error Code: -2)') % e
            tx.write({
                'state': 'error',
                'state_message': message,
                'last_state_change': fields.Datetime.now(),
            })
            return {'error': message}

    @route(['/pos/physical/cancel'], type='json', auth='user')
    def pos_physical_cancel(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().browse(kwargs['id'])
        self._pos_physical_cancel(tx)
        return {'status': 0}

    @route(['/pos/physical/query'], type='json', auth='user')
    def pos_physical_query(self, **kwargs):
        tx = request.env['payment.transaction'].sudo().browse(kwargs['id'])
        if tx:
            if tx.state == 'done':
                return {'status': 0, 'id': tx.id}
            elif tx.state != 'pending':
                return {'status': -1, 'message': tx.state_message}
            return {'status': 1}
        return {'status': -1, 'message': _('Transaction not found')}

    @route(['/pos/physical/result'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False)
    def pos_physical_result(self, **kwargs):
        try:
            result = json.loads(request.httprequest.data)
            order_id = result['order_id']
        except Exception as e:
            _logger.error('An error occured while processing PoS terminal response\n%s' % e)
            return

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', order_id)], limit=1)
        if not tx:
            _logger.error('An error occured while processing PoS terminal response\nTransaction not found with order_id %s' % order_id)
            return

        if 'Document' in result:
            tx.write({
                'state': 'done',
                'last_state_change': fields.Datetime.now(),
                'state_message': _('Transaction is successful')
            })
        else:
            tx.write({
                'state': 'error',
                'last_state_change': fields.Datetime.now(),
                'state_message': _('Transaction is failed')
            })
