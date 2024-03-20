# -*- coding: utf-8 -*-
import werkzeug
import json
import requests
import uuid
import base64
import hashlib
import logging
import re
from collections import OrderedDict

from odoo import fields, models, http, SUPERUSER_ID, _
from odoo.http import request
from odoo.tools.misc import formatLang
from odoo.tools.float_utils import float_compare, float_round
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal

_logger = logging.getLogger(__name__)


class PaymentPortal(portal.PaymentPortal):

    @http.route('/my/payment_method', type='http', methods=['GET'], auth='user', website=True)
    def payment_method(self, **kwargs):
        """
        We don't use payment tokens yet, so redirect 404
        """
        raise werkzeug.exceptions.NotFound()


class PayloxController(http.Controller):

    @staticmethod
    def _get(key, default=None):
        try:
            data = request.session['_paylox_%s' % key]
            if data == '0d':
                res = {}
                for r, v in request.session.items():
                    k = '_paylox_%s_' % key
                    if r.startswith(k):
                        res.update({r.replace(k, ''): v})

                if not res:
                    return data
                return res
            else:
                return data
        except:
            return default

    @staticmethod
    def _set(key, value):
        try:
            if isinstance(value, dict):
                request.session['_paylox_%s' % key] = '0d'
                for k, v in value.items():
                    request.session['_paylox_%s_%s' % (key, k)] = v
            else:
                request.session['_paylox_%s' % key] = value
        except:
            pass

    @staticmethod
    def _del(key=None):
        try:
            if not key:
                ks = []
                for k in request.session.keys():
                    if k.startswith('_paylox'):
                        ks.append(k)
                for k in ks:
                    del request.session[k]
            else:
                data = request.session['_paylox_%s' % key]
                if data == '0d':
                    ks = []
                    for k in request.session.keys():
                        if k.startswith('_paylox_%s_' % key):
                            ks.append(k)
                    for k in ks:
                        del request.session[k]
                del request.session['_paylox_%s' % key]
        except:
            pass

    @staticmethod
    def _get_acquirer(acquirer=None, providers=['jetcheckout'], limit=1):
        if acquirer == None:
            acquirer = PayloxController._get('acquirer')
            if acquirer:
                return request.env['payment.acquirer'].sudo().browse(acquirer)

        if acquirer:
            if isinstance(acquirer, int):
                return request.env['payment.acquirer'].sudo().browse(acquirer)
            else:
                return acquirer
        else:
            acquirer = request.env['payment.acquirer'].sudo()._get_acquirer(website=request.website, providers=providers, limit=limit)
            PayloxController._set('acquirer', acquirer.id)
            return acquirer

    @staticmethod
    def _get_campaigns(acquirer=None):
        acquirer = acquirer or PayloxController._get_acquirer()
        return request.env['payment.acquirer.jetcheckout.campaign'].sudo().search_read([('acquirer_id', '=', acquirer.id)], ['id', 'name'])

    @staticmethod
    def _get_campaign(acquirer=None, partner=None, transaction=None):
        campaign = PayloxController._get('campaign')
        if not campaign:
            if acquirer:
                campaign = acquirer.jetcheckout_campaign_id.name
            elif transaction:
                campaign = transaction.jetcheckout_campaign_name
            elif partner:
                campaign = partner.campaign_id.name
            else:
                campaign = ''
            PayloxController._set('campaign', campaign)
        return campaign

    @staticmethod
    def _get_currency(currency=None, acquirer=None):
        if currency:
            acquirer = acquirer or PayloxController._get_acquirer()
            if acquirer.currency_ids:
                if currency not in acquirer.currency_ids.ids:
                    raise Exception(_('The currency is not available.'))
                else:
                    currency = request.env['res.currency'].sudo().browse(currency)
                    PayloxController._set('currency', currency.id)
                    return currency
            else:
                if currency != request.env.company.currency_id.id:
                    raise Exception(_('The currency is not available.'))
            
        cid = PayloxController._get('currency')
        if not cid:
            currency = request.env.company.currency_id
            PayloxController._set('currency', currency.id)
            return currency
        else:
            return request.env['res.currency'].sudo().browse(cid)

    @staticmethod
    def _get_partner(pid=None, parent=None):
        partners = request.env['res.partner'].sudo()
        if not pid:
            pid = PayloxController._get('partner')
            if pid:
                partner = partners.browse(pid)
            else:
                partner = request.env.user.partner_id
        else:
            if isinstance(pid, int):
                partner = partners.browse(pid)
            elif isinstance(pid, str):
                partner = partners.browse(pid)
            elif isinstance(pid, models.Model):
                partner = pid
            else:
                partner = request.env.user.partner_id

        PayloxController._set('partner', partner.id)
        if parent:
            return partner.commercial_partner_id
        return partner

    @staticmethod
    def _get_type(t=None):
        type = PayloxController._get('type')
        if not type:
            if request.env.company.payment_page_campaign_table_ok:
                if request.env.company.payment_page_campaign_table_transpose:
                    type = 'ct'
                else:
                    type = 'c'
            else:
                type = 'i'
            PayloxController._set('type', type)
        return type == t if t else type

    @staticmethod
    def _get_installment_description(installment):
        if installment['plus_installment'] > 0:
            if installment['plus_installment_description']:
                return '%s + %s (%s)' % (installment['installment_count'], installment['plus_installment'], installment['plus_installment_description'])
            else:
                return '%s + %s' % (installment['installment_count'], installment['plus_installment'])
        return '%s' % installment['installment_count']

    @staticmethod
    def _get_validity(acquirer=None, number=None):
        acquirer = acquirer or PayloxController._get_acquirer()
        url = '%s/api/v1/prepayment/card_check' % acquirer._get_paylox_api_url()
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "card_number": number,
            "language": "tr",
        }

        try:
            response = requests.post(url, data=json.dumps(data), timeout=5)
            if response.status_code == 200:
                result = response.json()
                return result['response_code'] == "00" and result.get('card_valid')
            else:
                return False
        except:
            return False

    def _check_user(self):
        return True

    def _get_tx_vals(self, **kwargs):
        return {'jetcheckout_payment_ok': kwargs.get('payment_ok', True)}

    def _prepare(self, acquirer=None, company=None, partner=None, currency=None, transaction=None, balance=True):
        acquirer = self._get_acquirer(acquirer=acquirer)
        company = company or request.env.company
        currency = currency or (transaction and transaction.currency_id) or company.currency_id

        user = not request.env.user.share
        partner = self._get_partner(partner)
        partner_commercial = partner.commercial_partner_id
        partner_contact = partner if partner.parent_id else False
        type = self._get_type()

        campaign = self._get_campaign(partner=partner, transaction=transaction)
        card_family = self._get_card_family(acquirer=acquirer, campaign=campaign)
        currencies = acquirer.currency_ids
        if currencies and currency not in currencies:
            currency = currencies[0]

        values = {
            'ok': True,
            'partner': partner_commercial,
            'partner_name': partner_commercial.name,
            'contact': partner_contact,
            'acquirer': acquirer,
            'company': company,
            'campaign': campaign,
            'user': user,
            'type': type,
            'currency': currency,
            'currencies': currencies,
            'card_family': card_family,
            'no_terms': acquirer.jetcheckout_no_terms,
            'no_smart_buttons': acquirer.jetcheckout_no_smart_buttons,
        }
        if balance:
            balance = partner_commercial.credit - partner_commercial.debit
            balance_str = formatLang(request.env, abs(balance), currency_obj=currency)
            balance_sign = float_compare(balance, 0.0, precision_rounding=currency.rounding) < 0
            values.update({
                'balance': balance,
                'partner_balance': balance_str,
                'partner_balance_sign': balance_sign,
                'partner_balance_sign_str': balance_sign and _('Credit')[0] or _('Debit')[0],
                'partner_balance_sign_title': balance_sign and _('Credit') or _('Debit'),
            })
        return values

    def _get_card_type(self, type):
        if type == 'Credit':
            return _('Credit Card')
        elif type == 'Debit':
            return _('Debit Card')
        elif type == 'Credit-Business':
            return _('Business Card')
        else:
            return _('General')

    def _prepare_installment(self, acquirer=None, partner=0, amount=0, rate=0, currency=None, campaign='', bin='', **kwargs):
        self._check_user()
        client = self._get_partner(partner, parent=True)
        if not request.env.user.has_group('base.group_user'):
            if client and client.campaign_id:
                campaign = client.campaign_id.name

        acquirer = self._get_acquirer(acquirer=acquirer)
        currency =  self._get_currency(currency, acquirer)
        type = self._get_type()
        url = '%s/api/v1/prepayment/%sinstallment_options' % (acquirer._get_paylox_api_url(), bin and 'bin_' or '')
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            #"amount": int(float_round(amount, 2) * 100),
            "currency": currency.name,
            "language": "tr",
        }
        if bin:
            data.update({"bin": bin})

        if type == 'i':
            data.update({
                "campaign_name": campaign or self._get_campaign() or acquirer._get_campaign_name(int(partner))
            })

        values = {'type': type}

        response = requests.post(url, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()

            if result['response_code'] == "00":
                if type.startswith('i'):
                    if bin:
                        ids = list()
                        rows = list()

                        options = result.get('installments')
                        if not options:
                            return {'error': _('No installment found (Error Code: -1)')}

                        option = options[0]
                        values.update({
                            'card': {
                                'type': option.get('card_type', ''),
                                'currency': option.get('currency', ''),
                                'family': option.get('card_family', ''),
                                'logo': option.get('card_family_logo', ''),
                                'campaign': option.get('campaign_name', ''),
                                'excluded': option.get('excluded_bins', []),
                            }
                        })

                        for installment in option['installments']:
                            if installment['installment_count'] not in ids:
                                ids.append(installment['installment_count'])
                                rows.append({
                                    'id': installment['installment_count'],
                                    'amount': installment['installment_amount'],
                                    'crate': installment['customer_rate'],
                                    'corate': installment['cost_rate'],
                                    'min': installment['min_amount'],
                                    'max': installment['max_amount'],
                                    'plus': installment['plus_installment'],
                                    'pdesc': installment['plus_installment_description'],
                                    'idesc': self._get_installment_description(installment),
                                    'count': installment['installment_count'] + installment['plus_installment'],'irate': -rate if rate > 0 and installment['installment_count'] == 1 else 0.0,
                                })

                        rows.sort(key=lambda x: x['id'])
                        values.update({'rows': rows})

                    else:
                        tabs = set()
                        grids = OrderedDict()

                        options = result.get('installment_options')
                        if not options:
                            return {'error': _('No installment found (Error Code: -1)')}

                        campaign = options[0].get('campaign_name', '')
                        for option in options:
                            if option.get('campaign_name', '') != campaign:
                                continue

                            grid = {
                                'lines': [],
                                'campaign': campaign,
                                'type': option.get('card_type', ''),
                                'currency': option.get('currency', ''),
                                'family': option.get('card_family', ''),
                                'logo': option.get('card_family_logo', ''),
                                'excluded': option.get('excluded_bins', []),
                            }

                            tabs.add(grid['type'])

                            if grid['type'] not in grids:
                                grids[grid['type']] = []

                            ids = list()
                            for installment in option['installments']:
                                if installment['installment_count'] in ids:
                                    continue

                                line = {
                                    'id': installment['installment_count'],
                                    'amount': installment['installment_amount'],
                                    'crate': installment['customer_rate'],
                                    'corate': installment['cost_rate'],
                                    'min': installment['min_amount'],
                                    'max': installment['max_amount'],
                                    'plus': installment['plus_installment'],
                                    'pdesc': installment['plus_installment_description'],
                                    'idesc': self._get_installment_description(installment),
                                    'count': installment['installment_count'] + installment['plus_installment'],'irate': -rate if rate > 0 and installment['installment_count'] == 1 else 0.0,
                                }
                                ids.append(line['id'])
                                grid['lines'].append(line)

                            grid['lines'].sort(key=lambda x: x['id'])
                            grids[grid['type']].append(grid)

                        values.update({
                            'tabs': sorted(list(tabs)),
                            'grids': grids,
                        })

                elif type.startswith('c'):
                    included_campaigns = False
                    excluded_campaigns = False
                    client_campaigns = client and set(client.campaign_ids.mapped('name')) or set()
                    company_campaigns = set(acquirer.company_id.payment_page_campaign_table_ids.mapped('name'))
                    if acquirer.company_id.payment_page_campaign_table_included:
                        if client_campaigns and company_campaigns:
                            #included_campaigns = client_campaigns.intersection(company_campaigns)
                            included_campaigns = client_campaigns
                        elif not client_campaigns and company_campaigns:
                            included_campaigns = company_campaigns
                        elif client_campaigns and not company_campaigns:
                            included_campaigns = client_campaigns
                        else:
                            included_campaigns = set()
                    else:
                        if client_campaigns and company_campaigns:
                            #included_campaigns = client_campaigns.difference(company_campaigns)
                            included_campaigns = client_campaigns
                        elif not client_campaigns and company_campaigns:
                            excluded_campaigns = company_campaigns
                        elif client_campaigns and not company_campaigns:
                            included_campaigns = client_campaigns
                        else:
                            excluded_campaigns = set()

                    if 't' in type:
                        if bin:
                            cols = list()
                            rows = list()

                            options = result.get('installment_options', result.get('installments', []))
                            for option in options:
                                campaign = option.get('campaign_name', '')
                                if included_campaigns is not False and campaign not in included_campaigns:
                                    continue
                                if excluded_campaigns is not False and campaign in excluded_campaigns:
                                    continue

                                cols.append(campaign)
                                values.update({
                                    'card': {
                                        'type': option.get('card_type', ''),
                                        'currency': option.get('currency', ''),
                                        'family': option.get('card_family', ''),
                                        'logo': option.get('card_family_logo', ''),
                                        'excluded': option.get('excluded_bins', []),
                                    }
                                })

                                for installment in option['installments']:
                                    rows.append({
                                        'campaign': campaign,
                                        'id': installment['installment_count'],
                                        'amount': installment['installment_amount'],
                                        'crate': installment['customer_rate'],
                                        'corate': installment['cost_rate'],
                                        'min': installment['min_amount'],
                                        'max': installment['max_amount'],
                                        'plus': installment['plus_installment'],
                                        'pdesc': installment['plus_installment_description'],
                                        'idesc': self._get_installment_description(installment),
                                        'count': installment['installment_count'] + installment['plus_installment'],
                                        'irate': -rate if rate > 0 and installment['installment_count'] == 1 else 0.0,
                                    })
                                    break
                            values.update({'cols': cols, 'rows': rows})

                        else:
                            tabs = set()
                            rows = set()
                            cols = dict()
                            lines = OrderedDict()

                            options = result.get('installment_options', result.get('installments', []))
                            for option in options:
                                campaign = option.get('campaign_name', '')
                                if included_campaigns is not False and campaign not in included_campaigns:
                                    continue
                                if excluded_campaigns is not False and campaign in excluded_campaigns:
                                    continue

                                line = {
                                    'type': option.get('card_type', ''),
                                    'currency': option.get('currency', ''),
                                    'family': option.get('card_family', ''),
                                    'logo': option.get('card_family_logo', ''),
                                    'campaign': option.get('campaign_name', ''),
                                    'excluded': option.get('excluded_bins', []),
                                }

                                tabs.add(line['type'])
                                rows.add(line['campaign'])
                                cols.update({
                                    line['family']: {
                                        'family': line['family'],
                                        'logo': line['logo'],
                                    }
                                })

                                if line['type'] not in lines:
                                    lines[line['type']] = OrderedDict()
                                if line['campaign'] not in lines[line['type']]:
                                    lines[line['type']][line['campaign']] = {}
                                if line['family'] not in lines[line['type']][line['campaign']]:
                                    lines[line['type']][line['campaign']][line['family']] = []

                                lines[line['type']][line['campaign']][line['family']] += [{
                                    'type': line['type'],
                                    'family': line['family'],
                                    'campaign': line['campaign'],
                                    'id': installment['installment_count'],
                                    'amount': installment['installment_amount'],
                                    'crate': installment['customer_rate'],
                                    'corate': installment['cost_rate'],
                                    'min': installment['min_amount'],
                                    'max': installment['max_amount'],
                                    'plus': installment['plus_installment'],
                                    'pdesc': installment['plus_installment_description'],
                                    'idesc': self._get_installment_description(installment),
                                    'count': installment['installment_count'] + installment['plus_installment'],
                                    'irate': -rate if rate > 0 and installment['installment_count'] == 1 else 0.0
                                } for installment in option['installments']]

                            values.update({
                                'tabs': sorted(list(tabs)),
                                'rows': list(rows),
                                'cols': list(cols.values()),
                                'lines': lines,
                            })
                    else:
                        if bin:
                            cols = []
                            rows = []
                            index = -1
                            ids = OrderedDict()
                            options = result.get('installment_options', result.get('installments', []))
                            for option in options:
                                campaign = option.get('campaign_name', '')
                                if included_campaigns is not False and campaign not in included_campaigns:
                                    continue
                                if excluded_campaigns is not False and campaign in excluded_campaigns:
                                    continue

                                cols.append(campaign)
                                values.update({
                                    'card': {
                                        'type': option.get('card_type', ''),
                                        'currency': option.get('currency', ''),
                                        'family': option.get('card_family', ''),
                                        'logo': option.get('card_family_logo', ''),
                                        'excluded': option.get('excluded_bins', []),
                                    }
                                })

                                index += 1
                                for installment in option['installments']:
                                    id = installment['installment_count']
                                    if id not in ids:
                                        ids[id] = OrderedDict()

                                    if index in ids[id]:
                                        continue

                                    ids[id][index] = {
                                        'id': id,
                                        'index': index,
                                        'campaign': campaign,
                                        'amount': installment['installment_amount'],
                                        'crate': installment['customer_rate'],
                                        'corate': installment['cost_rate'],
                                        'min': installment['min_amount'],
                                        'max': installment['max_amount'],
                                        'plus': installment['plus_installment'],
                                        'pdesc': installment['plus_installment_description'],
                                        'idesc': self._get_installment_description(installment),
                                        'count': installment['installment_count'] + installment['plus_installment'],
                                        'irate': -rate if rate > 0 and installment['installment_count'] == 1 else 0.0,
                                    }

                            idl = list(ids.keys())
                            idl.sort()
                            for i in idl:
                                rows.append({
                                    'id': i,
                                    'ids': [ids[i].get(j, {'id': 0}) for j in range(index+1)]
                                })
                            values.update({'cols': cols, 'rows': rows})

                        else:
                            tabs = set()
                            rows = set()
                            cols = dict()
                            lines = OrderedDict()

                            options = result.get('installment_options', result.get('installments', []))
                            for option in options:
                                campaign = option.get('campaign_name', '')
                                if included_campaigns is not False and campaign not in included_campaigns:
                                    continue
                                if excluded_campaigns is not False and campaign in excluded_campaigns:
                                    continue

                                line = {
                                    'type': option.get('card_type', ''),
                                    'currency': option.get('currency', ''),
                                    'family': option.get('card_family', ''),
                                    'logo': option.get('card_family_logo', ''),
                                    'campaign': option.get('campaign_name', ''),
                                    'excluded': option.get('excluded_bins', []),
                                }

                                tabs.add(line['type'])
                                rows.add(line['campaign'])
                                cols.update({
                                    line['family']: {
                                        'logo': line['logo'],
                                        'family': line['family'],
                                    }
                                })

                                if line['type'] not in lines:
                                    lines[line['type']] = OrderedDict()
                                if line['campaign'] not in lines[line['type']]:
                                    lines[line['type']][line['campaign']] = {}
                                if line['family'] not in lines[line['type']][line['campaign']]:
                                    lines[line['type']][line['campaign']][line['family']] = []

                                lines[line['type']][line['campaign']][line['family']] += [{
                                    'type': line['type'],
                                    'family': line['family'],
                                    'campaign': line['campaign'],
                                    'id': installment['installment_count'],
                                    'amount': installment['installment_amount'],
                                    'crate': installment['customer_rate'],
                                    'corate': installment['cost_rate'],
                                    'min': installment['min_amount'],
                                    'max': installment['max_amount'],
                                    'plus': installment['plus_installment'],
                                    'pdesc': installment['plus_installment_description'],
                                    'idesc': self._get_installment_description(installment),
                                    'count': installment['installment_count'] + installment['plus_installment'],
                                    'irate': -rate if rate > 0 and installment['installment_count'] == 1 else 0.0
                                } for installment in option['installments']]

                            values.update({
                                'tabs': sorted(list(tabs)),
                                'rows': list(rows),
                                'cols': list(cols.values()),
                                'lines': lines,
                            })

            elif result['response_code'] == "00104":
                pass
            else:
                values = {'error': _('%s (Error Code: %s)') % (result['message'], result['response_code'])}
        else:
            values = {'error': _('%s (Error Code: %s)') % (response.reason, response.status_code)}
        return values

    @staticmethod
    def _get_campaigns_all(**kwargs):
        acquirer = PayloxController._get_acquirer(acquirer=kwargs['acquirer'])
        currency = request.env.company.currency_id
        url = '%s/api/v1/prepayment/installment_options' % acquirer._get_paylox_api_url()
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            "currency": currency.name,
            "language": "tr",
            "is_3d": True,
        }

        try:
            response = requests.post(url, data=json.dumps(data), timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == "00":
                    installments = result.get('installment_options', [])
                    campaigns = []
                    for installment in installments:
                        if installment['campaign_name'] not in campaigns:
                            campaigns.append(installment['campaign_name'])
                    return campaigns
                else:
                    return []
            else:
                return []
        except:
            return []

    @staticmethod
    def _get_card_family(**kwargs):
        acquirer = PayloxController._get_acquirer(acquirer=kwargs['acquirer'])
        currency = request.env.company.currency_id
        url = '%s/api/v1/prepayment/installment_options' % acquirer._get_paylox_api_url()
        pid = 'partner' in kwargs and int(kwargs['partner']) or None
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            "currency": currency.name,
            "campaign_name": kwargs['campaign'] or acquirer._get_campaign_name(pid),
            "language": "tr",
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
 
    @staticmethod
    def _get_bank_codes(**kwargs):
        acquirer = PayloxController._get_acquirer(acquirer=kwargs['acquirer'])
        url = '%s/api/v1/prepayment/bankcodes' % acquirer._get_paylox_api_url()
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "language": "tr",
        }

        try:
            response = requests.post(url, data=json.dumps(data), timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result['response_code'] == "00":
                    return result.get('bank_codes', [])
                else:
                    return []
            else:
                return []
        except:
            return []

    def _get_transaction(self):
        return False

    def _process(self, **kwargs):
        if 'order_id' not in kwargs:
            return '/404', None, True

        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', kwargs.get('order_id'))], limit=1)
        if not tx:
            return '/404', None, True

        url = kwargs.get('result_url', '/payment/card/result')
        tx.with_context(domain=request.httprequest.referrer)._paylox_query({
            'successful': kwargs.get('response_code') == '00',
            'code': kwargs.get('response_code', ''),
            'message': kwargs.get('response_message', ''),
            'amount': kwargs.get('amount', 0),
            'vpos_id': kwargs.get('virtual_pos_id', ''),
            'vpos_name': kwargs.get('virtual_pos_name', ''),
            'vpos_code': kwargs.get('auth_code', ''),
            'commission_rate': float(kwargs.get('expected_cost_rate', 0)),
        })
        return url, tx, False

    @http.route('/payment/card/acquirer', type='json', auth='user', website=True)
    def payment_acquirer(self):
        acquirer = self._get_acquirer()
        commission = request.env['ir.model.data'].sudo()._xmlid_to_res_id('payment_jetcheckout.product_commission')
        return {
            'id': acquirer.id,
            'campaign': acquirer.jetcheckout_campaign_id.name,
            'product': {
                'commission': commission,
            }
        }

    @http.route('/payment/card/type', type='json', auth='user', website=True)
    def payment_card_type(self, acquirer=False):
        acquirer = self._get_acquirer(acquirer=acquirer)
        if acquirer:
            return [{'id': icon.id, 'name': icon.name, 'src': icon.image} for icon in acquirer.payment_icon_ids]
        return []

    @http.route('/payment/card/family', type='json', auth='user', website=True)
    def payment_card_family(self, **kwargs):
        acquirer = self._get_acquirer(acquirer=kwargs['acquirer'])
        if acquirer:
            return self._get_card_family(**kwargs)
        return []
 
    @http.route('/payment/card/banks', type='json', auth='user', website=True)
    def payment_card_banks(self, **kwargs):
        acquirer = self._get_acquirer(acquirer=kwargs['acquirer'])
        if acquirer:
            return self._get_bank_codes(**kwargs)
        return []

    @http.route(['/pay'], type='http', auth='user', website=True)
    def payment_page(self, **kwargs):
        values = self._prepare()
        if not values['acquirer'].jetcheckout_payment_page:
            raise werkzeug.exceptions.NotFound()
        return request.render('payment_jetcheckout.page_payment', values)

    @http.route(['/payment/card/campaigns'], type='json', auth='user', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def get_campaigns(self, **kwargs):
        campaigns = [{'id': 0, 'name': ''}]
        campaigns.extend(self._get_campaigns())
        return campaigns

    @http.route(['/payment/card/installments'], type='json', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def get_installments(self, **kwargs):
        return self._prepare_installment(**kwargs)

    @http.route(['/payment/card/installment'], type='json', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, website=True)
    def get_installment(self, **kwargs):
        return self._prepare_installment(**kwargs)

    @http.route('/payment/card/valid', type='json', auth='public', csrf=False, sitemap=False, website=True)
    def payment_card_valid(self, number):
        return self._get_validity(number=number)

    @http.route(['/payment/card/pay'], type='json', auth='public', csrf=False, sitemap=False, website=True)
    def payment(self, **kwargs):
        self._check_user()

        rows = kwargs['installment']['rows']
        installment = kwargs['installment']['id']
        campaign = kwargs.get('campaign', '')

        amount = float(kwargs['amount'])
        rate = float(kwargs.get('discount', {}).get('single', 0))
        if rate > 0 and installment == 1:
            amount = amount * (100 - rate) / 100

        type = self._get_type()
        if type == 'c':
            index = kwargs['installment']['index']
            installment = next(filter(lambda x: x['id'] == installment, rows), None)
            installment = next(filter(lambda x: x['index'] == index, installment['ids']), None)
        elif type == 'ct':
            index = kwargs['installment']['id']
            installment = next(filter(lambda x: x['id'] == index and x['campaign'] == campaign, rows), None)
        else:
            installment = next(filter(lambda x: x['id'] == installment, rows), None)

        amount_customer = amount * installment['crate'] / 100
        amount_total = float_round(amount + amount_customer, 2)
        amount_cost = float_round(amount_total * installment['corate'] / 100, 2)
        amount_integer = round(amount_total * 100)

        acquirer = self._get_acquirer()
        currency = self._get_currency(kwargs['currency'], acquirer)
        partner = self._get_partner(kwargs['partner'], parent=True)
        year = str(fields.Date.today().year)[:2]
        hash = base64.b64encode(hashlib.sha256(''.join([acquirer.jetcheckout_api_key, str(kwargs['card']['number']), str(amount_integer), acquirer.jetcheckout_secret_key]).encode('utf-8')).digest()).decode('utf-8')
        data = {
            "application_key": acquirer.jetcheckout_api_key,
            "mode": acquirer._get_paylox_env(),
            "campaign_name": campaign,
            "amount": amount_integer,
            "currency": currency.name,
            "installment_count": installment['count'],
            "card_number": kwargs['card']['number'],
            "expire_month": kwargs['card']['date'][:2],
            "expire_year": year + kwargs['card']['date'][-2:],
            "is_3d": True,
            "hash_data": hash,
            "language": "tr",
        }

        if getattr(partner, 'tax_office_id', False):
            data.update({'billing_tax_office': partner.tax_office_id.name})
        elif getattr(partner, 'tax_office', False):
            data.update({'billing_tax_office': partner.tax_office})

        if partner.vat:
            partner_vat = re.sub(r'[^\d]', '', partner.vat)
            if partner_vat and len(partner_vat) in (10, 11):
                data.update({'billing_tax_number': partner_vat})

        order_id = str(uuid.uuid4())
        sale_id = int(kwargs.get('order', 0))
        invoice_id = int(kwargs.get('invoice', 0))

        tx = self._get_transaction()
        vals = {
            'acquirer_id': acquirer.id,
            'callback_hash': hash,
            'amount': amount_total,
            'fees': amount_cost,
            'operation': 'online_direct',
            'jetcheckout_website_id': request.website.id,
            'jetcheckout_ip_address': tx and tx.jetcheckout_ip_address or request.httprequest.remote_addr,
            'jetcheckout_url_address': tx and tx.jetcheckout_url_address or request.httprequest.referrer,
            'jetcheckout_campaign_name': campaign,
            'jetcheckout_card_name': kwargs['card']['holder'],
            'jetcheckout_card_number': ''.join([kwargs['card']['number'][:6], '*'*6, kwargs['card']['number'][-4:]]),
            'jetcheckout_card_type': kwargs['card']['type'].capitalize(),
            'jetcheckout_card_family': kwargs['card']['family'].capitalize(),
            'jetcheckout_order_id': order_id,
            'jetcheckout_payment_amount': amount,
            'jetcheckout_installment_count': installment['count'],
            'jetcheckout_installment_plus': installment['plus'],
            'jetcheckout_installment_description': installment['idesc'],
            'jetcheckout_installment_amount': amount / installment['count'] if installment['count'] > 0 else amount,
            'jetcheckout_commission_rate': installment['corate'],
            'jetcheckout_commission_amount': amount_cost,
            'jetcheckout_customer_rate': installment['crate'],
            'jetcheckout_customer_amount': amount_customer,
        }

        if tx:
            vals.update(self._get_tx_vals(**kwargs))
            tx.write(vals)
        else:
            vals.update({
                'amount': amount_total,
                'fees': amount_cost,
                'currency_id': currency.id,
                'acquirer_id': acquirer.id,
                'partner_id': partner.id,
                'operation': 'online_direct',
            })
            vals.update(self._get_tx_vals(**kwargs))
            tx = request.env['payment.transaction'].sudo().create(vals)

        if sale_id:
            tx.sale_order_ids = [(4, sale_id)]
            sale_order_id = request.env['sale.order'].sudo().browse(sale_id)
            billing_partner_id = sale_order_id.partner_invoice_id
            shipping_partner_id = sale_order_id.partner_shipping_id
            data.update({
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

            if not float_compare(amount, sale_order_id.amount_total, 2):
                customer_basket = [{
                    "id": line.product_id.default_code or str(line.product_id.id),
                    "name": line.product_id.name,
                    "description": line.name,
                    "qty": line.product_uom_qty,
                    "amount": line.price_total,
                    "category": line.product_id.categ_id.name,
                    "is_physical": line.product_id.type == 'product',
                } for line in sale_order_id.order_line if line.price_total > 0]

                if amount_customer > 0:
                    product = request.env.ref('payment_jetcheckout.product_commission').sudo()
                    customer_basket.append({
                        "id": product.default_code or str(product.id),
                        "name": product.display_name,
                        "description": product.name,
                        "qty": 1.0,
                        "amount": round(float_round(amount_customer, 2), 2), # used double round, because format_round seems not working
                        "category": product.categ_id.name,
                        "is_physical": False,
                    })
                data.update({"customer_basket": customer_basket})

        elif invoice_id:
            tx.invoice_ids = [(4, invoice_id)]

        self._set('tx', tx.id)

        url = '%s/api/v1/payment' % acquirer._get_paylox_api_url()
        fullname = tx.partner_name.split(' ', 1)
        address = []
        if tx.partner_city:
            address.append(tx.partner_city)
        if tx.partner_state_id:
            address.append(tx.partner_state_id.name)
        if tx.partner_country_id:
            address.append(tx.partner_country_id.name)

        base_url = request.httprequest.host
        success_url = '/payment/card/success' if 'successurl' not in kwargs or not kwargs['successurl'] else kwargs['successurl']
        fail_url = '/payment/card/fail' if 'failurl' not in kwargs or not kwargs['failurl'] else kwargs['failurl']
        data.update({
            "order_id": order_id,
            "card_holder_name": kwargs['card']['holder'],
            "cvc": kwargs['card']['code'],
            "success_url": "https://%s%s" % (base_url, success_url),
            "fail_url": "https://%s%s" % (base_url, fail_url),
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
            txid = result['transaction_id']
            if result['response_code'] in ("00", "00307"):
                rurl = result['redirect_url']
                tx.write({
                    'state': 'pending',
                    'state_message': _('Transaction is pending...'),
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
                    'acquirer_reference': txid,
                    'jetcheckout_transaction_id': txid,
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
    def finalize(self, **kwargs):
        kwargs['result_url'] = '/payment/card/result'
        url, tx, status = self._process(**kwargs)
        if not status and tx.jetcheckout_order_id:
            url += '?=%s' % tx.jetcheckout_order_id
        return werkzeug.utils.redirect(url)

    @http.route('/payment/card/custom/<int:record>/<string:access_token>', type='http', auth='public', methods=['GET', 'POST'], csrf=False, sitemap=False, save_session=False)
    def custom(self, **kwargs):
        kwargs['result_url'] = '/payment/confirmation'
        url, tx, status = self._process(**kwargs)
        token = payment_utils.generate_access_token(tx.partner_id.id, tx.amount, tx.currency_id.id)
        url += '?tx_id=%s&access_token=%s' % (tx.id, token)
        self._del()
        return werkzeug.utils.redirect(url)

    @http.route(['/payment/callback'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, website=True)
    def callback(self, **kwargs):
        try:
            data = json.loads(request.httprequest.data) or {}
            if data.get('is_success'):
                tx = request.env['payment.transaction'].sudo().search([
                    ('jetcheckout_order_id', '=', data.get('order_id')),
                    ('jetcheckout_transaction_id', '=', data.get('transaction_id')),
                ], limit=1)
                if tx:
                    tx._paylox_done_postprocess()
                    # tx.with_context(domain=request.httprequest.referrer)._paylox_query() # enable this line to resend query
        except Exception as e:
            _logger.error('An error occured when processing payment callback: %s' % e)

    @http.route(['/payment/card/result'], type='http', auth='public', methods=['GET'], website=True, csrf=False, sitemap=False)
    def result(self, **kwargs):
        values = self._prepare()
        if '' in kwargs:
            txid = re.split(r'\?|%3F', kwargs[''])[0]
            values['tx'] = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', txid)], limit=1)
        else:
            txid = self._get('tx', 0)
            values['tx'] = request.env['payment.transaction'].sudo().browse(txid)
        self._del()
        return request.render('payment_jetcheckout.page_result', values)

    @http.route(['/payment/card/terms'], type='json', auth='public', csrf=False, website=True)
    def terms(self, **kwargs):
        acquirer = self._get_acquirer()
        company = request.env.company
        domain = request.httprequest.referrer
        partner = self._get_partner(kwargs.get('partner'), parent=True)
        return acquirer.sudo().with_context(domain=domain)._render_paylox_terms(company.id, partner.id)

    @http.route(['/payment/card/report/<string:name>/<string:order>'], type='http', auth='public', methods=['GET'], csrf=False, website=True)
    def report(self, name, order, **kwargs):
        tx = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', order)], limit=1)
        if not tx:
            raise werkzeug.exceptions.NotFound()

        # Use following lines to get pdf report
        # pdf = request.env.ref('payment_jetcheckout.report_%s' % name).with_user(SUPERUSER_ID)._render_qweb_pdf([tx.id])[0]
        # pdfhttpheaders = [
        #     ('Content-Type', 'application/pdf'),
        #     ('Content-Length', len(pdf)),
        # ]
        #return request.make_response(pdf, headers=pdfhttpheaders)
        html = request.env.ref('payment_jetcheckout.report_%s' % name).with_user(SUPERUSER_ID)._render_qweb_html([tx.id])[0]
        return request.make_response(html)

    @http.route(['/payment/card/transactions', '/payment/card/transactions/page/<int:page>'], type='http', auth='user', website=True)
    def transactions(self, page=0, tpp=20, **kwargs):
        values = self._prepare()
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
        return request.render('payment_jetcheckout.page_transaction', values)

    @http.route(['/payment/card/ledger', '/payment/card/ledger/page/<int:page>'], type='http', auth='user', website=True)
    def ledger(self, page=0, tpp=40, **kwargs):
        values = self._prepare()
        partner = request.env.user.partner_id
        aml_ids = request.env['account.move.line'].sudo().search([
            ('company_id', '=', values['company'].id),
            ('partner_id', 'in', (partner.id, partner.commercial_partner_id.id)),
            ('account_internal_type', 'in', ('receivable', 'payable')),
            ('parent_state', '=', 'posted')
        ])
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
        return request.render('payment_jetcheckout.page_ledger', values)
