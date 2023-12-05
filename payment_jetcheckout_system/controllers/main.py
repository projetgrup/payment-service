# -*- coding: utf-8 -*-
import werkzeug
import base64
import re
from urllib.parse import urlparse
from datetime import date

from odoo import fields, http, _
from odoo.http import request
from odoo.tools import html_escape
from odoo.exceptions import AccessError, UserError
from odoo.addons.payment_jetcheckout.controllers.main import PayloxController as Controller


class PayloxSystemController(Controller):

    def _check_redirect(self, partner):
        if not request.env.user.share:
            return False

        if not partner.system:
            return False
 
        company_id = partner.company_id.id or request.env.company.id
        if not request.website.company_id.id == company_id:
            website = request.env['website'].sudo().search([('company_id', '=', company_id)], limit=1)
            if website:
                path = urlparse(request.httprequest.url).path
                return werkzeug.utils.redirect(website.domain + path)
            else:
                raise werkzeug.exceptions.NotFound()
        return False

    def _check_user(self):
        path = urlparse(request.httprequest.referrer).path
        if '/my/payment' in path and not request.env.user.active and request.website.user_id.id != request.env.user.id:
            raise AccessError(_('Access Denied'))
        return super()._check_user()

    def _check_payment_page(self):
        if not request.env.company.payment_page_ok:
            raise werkzeug.exceptions.NotFound()
        if not request.env.user.share and not request.env.user.payment_page_ok:
            raise werkzeug.exceptions.NotFound()

    def _check_payment_preview_page(self):
        if request.env.user.share or not request.env.user.payment_preview_ok or not request.env.company.payment_page_ok or not request.env.company.payment_advance_ok:
            raise werkzeug.exceptions.NotFound()

    def _check_advance_page(self, **kwargs):
        if not request.env.company.payment_advance_ok:
            raise werkzeug.exceptions.NotFound()

        if request.env.user.share and not 'id' in kwargs:
            raise werkzeug.exceptions.NotFound()

    def _get_parent(self, token):
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            raise werkzeug.exceptions.NotFound()

        websites = request.env['website'].sudo().search([('domain', 'like', '%%%s%%' % request.httprequest.host)])
        companies = websites.mapped('company_id')
        partner = request.env['res.partner'].sudo().search([
            ('id', '=', id), ('access_token', '=', token),
            '|',('company_id', '=', False), ('company_id', 'in', companies.ids),
        ], limit=1)
        if not partner:
            raise werkzeug.exceptions.NotFound()

        return partner

    def _get_tx_vals(self, **kwargs):
        vals = super()._get_tx_vals(**kwargs)
        ids = kwargs.get('payments', [])
        if ids:
            vals.update({'jetcheckout_item_ids': [(6, 0, ids)]})
        if request.env.company.system:
            vals.update({'jetcheckout_payment_ok': False})
        return vals

    def _process(self, **kwargs):
        url, tx, status = super()._process(**kwargs)
        if not status and (tx.company_id.system or tx.partner_id.system):
            status = True
            url = '%s?=%s' % (tx.partner_id._get_share_url(), kwargs.get('order_id'))
        return url, tx, status

    def _prepare(self, **kwargs):
        res = super()._prepare(**kwargs)
        res['companies'] = request.website._get_companies().sudo()
        return res

    def _prepare_system(self, company, system, partner, transaction):
        currency = company.currency_id
        acquirer = self._get_acquirer(False)
        type = self._get_type()
        campaign = transaction.jetcheckout_campaign_name if transaction else partner.campaign_id.name if partner else ''
        card_family = self._get_card_family(acquirer=acquirer, campaign=campaign)
        token = partner._get_token()
        companies = partner._get_companies()
        tags = partner._get_tags()
        return {
            'ok': True,
            'partner': partner,
            'partner_name': partner.name,
            'tags': tags,
            'company': company,
            'companies': companies,
            'website': request.website,
            'footer': request.website.payment_footer,
            'user': not request.env.user.share,
            'acquirer': acquirer,
            'campaign': campaign,
            'card_family': card_family,
            'success_url': '/payment/card/success',
            'fail_url': '/payment/card/fail',
            'date_empty': date(1, 1, 1),
            'tx': transaction,
            'system': system,
            'token': token,
            'type': type,
            'currency': currency,
            'no_terms': not acquirer.provider == 'jetcheckout' or acquirer.jetcheckout_no_terms,
        }

    @http.route('/p/<token>', type='http', auth='public', methods=['GET'], csrf=False, sitemap=False, website=True)
    def page_system_link(self, token, **kwargs):
        partner = self._get_parent(token)
        transaction = None
        if '' in kwargs:
            txid = re.split(r'\?|%3F', kwargs[''])[0]
            transaction = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', txid)], limit=1)
            if not transaction:
                raise werkzeug.exceptions.NotFound()

        company = partner.company_id or request.website.company_id or request.env.company
        if not company == request.env.company:
            website = request.env['website'].sudo().search([('company_id', '=', company.id)], limit=1)
            if not website:
                raise werkzeug.exceptions.NotFound()

            website._force()
            return request.redirect(request.httprequest.url)

        system = company.system or partner.system or 'jetcheckout_system'
        values = self._prepare_system(company, system, partner, transaction)
        return request.render('payment_%s.page_payment' % system, values)

    @http.route('/p/<token>/<int:pid>', type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, website=True)
    def page_system_link_file(self, token, pid, **kwargs):
        partner = self._get_parent(token)
        payment = request.env['payment.item'].sudo().browse(pid)
        if not payment.parent_id.id == partner.id or payment.paid:
            raise werkzeug.exceptions.NotFound()

        pdf = payment.file
        if not pdf:
            raise werkzeug.exceptions.NotFound()

        pdf = base64.b64decode(pdf)
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'attachment; filename="%s.pdf"' % html_escape(payment.description)),
            ('Content-Length', len(pdf)),
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route(['/p/privacy'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_privacy_policy(self):
        return request.website.payment_privacy_policy

    @http.route(['/p/agreement'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_sale_agreement(self):
        return request.website.payment_sale_agreement

    @http.route(['/p/membership'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_membership_agreement(self):
        return request.website.payment_membership_agreement

    @http.route(['/p/contact'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_contact_page(self):
        return request.website.payment_contact_page

    @http.route(['/p/company'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_company(self, cid):
        if cid == request.env.company.id:
            return False

        token = request.httprequest.referrer.rsplit('/', 1).pop()
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            return False

        website = request.env['website'].sudo().search([
            ('domain', '=', request.website.domain),
            ('company_id', '=', cid)
        ], limit=1)
        if not website:
            return False

        partner = request.env['res.partner'].sudo().search([
            ('id', '=', id),
            ('access_token', '=', token),
            ('company_id', '=', request.env.company.id),
        ], limit=1)
        if not partner:
            return False

        partner = request.env['res.partner'].sudo().search([
            ('vat', '!=', False),
            ('vat', '=', partner.vat),
            ('company_id', '=', cid),
        ], limit=1)
        if not partner:
            return False

        website._force()
        return partner._get_token()

    @http.route(['/p/company/<int:id>/logo'], type='http', auth='public')
    def page_system_link_company_image(self, id):
        return request.env['ir.http'].sudo()._content_image(xmlid=None, model='res.company', res_id=id, field='logo', filename_field='name', unique=None, filename=None, mimetype=None, download=None, width=0, height=0, crop=False, quality=0, access_token=None)

    @http.route(['/p/tag'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_tag(self, tid):
        token = request.httprequest.referrer.rsplit('/', 1).pop()
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            return False

        partner = request.env['res.partner'].sudo().search([
            ('id', '=', id),
            ('access_token', '=', token),
            ('company_id', '=', request.env.company.id),
        ], limit=1)
        if not partner:
            return False

        if tid in partner.category_id.ids:
            return False

        partner = request.env['res.partner'].sudo().search([
            ('vat', '!=', False),
            ('vat', '=', partner.vat),
            ('category_id', 'in', [tid]),
            ('company_id', '=', request.env.company.id),
        ], limit=1)
        if not partner:
            return False

        return partner._get_token()

    @http.route(['/p/due'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_due(self, items):
        ids = [i[0] for i in items]
        amounts = dict(items)
        items = request.env['payment.item'].sudo().browse(ids)
        return items.with_context(amounts=amounts).get_due()

    @http.route(['/p/advance/add'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_advance_add(self, amount):
        if not request.env.company.payment_page_advance_ok:
            raise

        token = request.httprequest.referrer.rsplit('/', 1).pop()
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            raise

        partner = request.env['res.partner'].sudo().search([
            ('id', '=', id),
            ('access_token', '=', token),
            ('company_id', '=', request.env.company.id),
        ], limit=1)
        if not partner:
            raise

        item = request.env['payment.item'].sudo().search([
            ('advance', '=', True),
            ('parent_id', '=', partner.id),
            ('paid', '=', False)
        ])
        if item:
            item.write({
                'date': fields.Date.today(),
                'amount': item.amount + amount,
            })
        else:
            request.env['payment.item'].sudo().create({
                'parent_id': partner.id,
                'amount': amount,
                'advance': True,
                'description': _('Advance Payment'),
            })
        return True

    @http.route(['/p/advance/remove'], type='json', auth='public', website=True, csrf=False)
    def page_system_link_advance_remove(self, pid):
        token = request.httprequest.referrer.rsplit('/', 1).pop()
        id, token = request.env['res.partner'].sudo()._resolve_token(token)
        if not id or not token:
            raise

        partner = request.env['res.partner'].sudo().search([
            ('id', '=', id),
            ('access_token', '=', token),
            ('company_id', '=', request.env.company.id),
        ], limit=1)
        if not partner:
            raise

        request.env['payment.item'].sudo().search([
            ('id', '=', pid),
            ('parent_id', '=', partner.id),
            ('paid_amount', '=', 0)
        ]).unlink()
        return True

    @http.route('/my/advance', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_system_advance(self, **kwargs):
        self._check_advance_page(**kwargs)
        website_id = int(kwargs.get('id', request.website.id))
        if request.website.id != website_id:
            website = request.env['website'].sudo().browse(website_id)
            if not website:
                raise werkzeug.exceptions.NotFound()

            website._force()
            path = request.httprequest.path
            query = request.httprequest.query_string
            if query:
                path += '?' + query.decode('utf-8')
            return werkzeug.utils.redirect(path)

        company = request.env.company
        if 'currency' in kwargs and isinstance(kwargs['currency'], str) and len(kwargs['currency']) == 3:
            currency = request.env['res.currency'].sudo().search([('name', '=', kwargs['currency'])], limit=1)
        else:
            currency = None

        user = request.env.user
        if request.website.company_id.id != user.company_id.id:
            website = request.env['website'].sudo().search([
                ('domain', '=', request.website.domain),
                ('company_id', '=', user.company_id.id)
            ], limit=1)
            if not website:
                raise werkzeug.exceptions.NotFound()
            
            website._force()
            path = request.httprequest.path
            query = request.httprequest.query_string
            if query:
                path += '?' + query.decode('utf-8')
            return werkzeug.utils.redirect(path)

        partner = user.partner_id if user.has_group('base.group_portal') else request.website.user_id.partner_id.sudo()
        values = self._prepare(partner=partner, company=company, currency=currency)
        companies = values['companies']
        if user.share:
            companies = []
        else:
            companies = companies.filtered(lambda x: x.payment_advance_ok and x.id in user.company_ids.ids)

        values.update({
            'success_url': '/my/payment/success',
            'fail_url': '/my/payment/fail',
            'companies': companies,
            'system': company.system,
            'subsystem': company.subsystem,
            'vat': kwargs.get('vat'),
            'flow': 'dynamic',
            'advance': True,
            'readonly': user.share and company.payment_advance_amount_readonly,
        })

        if 'values' in kwargs and isinstance(kwargs['values'], dict):
            values.update({**kwargs['values']})

        try:
            values.update({'amount': float(kwargs['amount'])})
        except:
            pass

        # remove hash if exists
        # it could be there because of api module
        self._del('hash')

        return request.render('payment_jetcheckout_system.page_payment', values)

    @http.route('/my/payment/preview', type='http', auth='public', methods=['GET'], sitemap=False, csrf=False, website=True)
    def page_system_payment_preview(self, **kwargs):
        self._check_payment_preview_page()

        company = request.env.company
        values = self._prepare(company=company)
        values.update({
            'system': company.system,
            'subsystem': company.subsystem,
        })

        if 'values' in kwargs and isinstance(kwargs['values'], dict):
            values.update({**kwargs['values']})

        try:
            values.update({'amount': float(kwargs['amount'])})
        except:
            pass

        return request.render('payment_jetcheckout_system.page_payment_preview', values)

    @http.route('/my/payment', type='http', auth='public', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_system_payment(self, **kwargs):
        self._check_payment_page()

        if not kwargs.get('values', {}).get('no_redirect'):
            if request.env.user.has_group('base.group_public'):
                raise werkzeug.exceptions.NotFound()

            partner = request.env.user.partner_id
            redirect = self._check_redirect(partner)
            if redirect:
                return redirect

        company = request.env.company
        if 'currency' in kwargs and isinstance(kwargs['currency'], str) and len(kwargs['currency']) == 3:
            currency = request.env['res.currency'].sudo().search([('name', '=', kwargs['currency'])], limit=1)
        else:
            currency = None

        if 'pid' in kwargs:
            partner = self._get_parent(kwargs['pid'])
        elif 'vat' in kwargs and isinstance(kwargs['vat'], str) and 9 < len(kwargs['vat']) < 14:
            partner = request.env['res.partner'].sudo().search([
                ('vat', '!=', False),
                ('vat', '=', kwargs['vat']),
                ('company_id', '=', company.id),
                ('system', '=', company.system)
            ])
            if len(partner) != 1:
                partner = None
        elif company.payment_page_flow == 'dynamic':
            partner = request.website.user_id.partner_id.sudo()
        else:
            partner = None

        values = self._prepare(partner=partner, company=company, currency=currency)
        values.update({
            'success_url': '/my/payment/success',
            'fail_url': '/my/payment/fail',
            'system': company.system,
            'subsystem': company.subsystem,
            'flow': company.payment_page_flow,
            'vat': kwargs.get('vat'),
        })

        if 'values' in kwargs and isinstance(kwargs['values'], dict):
            values.update({**kwargs['values']})

        try:
            values.update({'amount': float(kwargs['amount'])})
        except:
            pass

        # remove hash if exists
        # it could be there because of api module
        self._del('hash')

        return request.render('payment_jetcheckout_system.page_payment', values)

    @http.route('/my/payment/<token>', type='http', auth='public', methods=['GET'], sitemap=False, website=True)
    def page_system_payment_login(self, token, **kwargs):
        self._check_payment_page()

        partner = self._get_parent(token)
        redirect = self._check_redirect(partner)
        if redirect:
            return redirect

        if partner.is_portal:
            if request.env.user.has_group('base.group_public'):
                user = partner.users_id
                request.session.authenticate(request.db, user.login, {'token': token})
            return request.render('payment_jetcheckout_system.page_login', {'token': token})
        else:
            return werkzeug.utils.redirect('/p/%s' % token)

    @http.route(['/my/payment/company'], type='json', auth='public', website=True, csrf=False)
    def page_system_page_company(self, cid):
        if cid == request.env.company.id:
            if request.session.get('company'):
                return False

        else:
            website = request.env['website'].sudo().search([
                ('domain', '=', request.website.domain),
                ('company_id', '=', cid)
            ], limit=1)
            if not website:
                return False
            website._force()

        request.session['company'] = True
        return True

    @http.route(['/my/payment/company/<int:id>/logo'], type='http', auth='public')
    def page_system_page_company_image(self, id):
        return request.env['ir.http'].sudo()._content_image(xmlid=None, model='res.company', res_id=id, field='logo', filename_field='name', unique=None, filename=None, mimetype=None, download=None, width=0, height=0, crop=False, quality=0, access_token=None)

    @http.route(['/my/payment/success', '/my/payment/fail'], type='http', auth='public', methods=['POST'], csrf=False, sitemap=False, save_session=False)
    def page_system_payment_return(self, **kwargs):
        kwargs['result_url'] = '/my/payment/result'
        url, tx, status = self._process(**kwargs)
        if not status and tx.jetcheckout_order_id:
            url += '?=%s' % tx.jetcheckout_order_id
        return werkzeug.utils.redirect(url)

    @http.route('/my/payment/result', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def page_system_payment_result(self, **kwargs):
        values = self._prepare()
        if '' in kwargs:
            txid = re.split(r'\?|%3F', kwargs[''])[0]
            values['tx'] = request.env['payment.transaction'].sudo().search([('jetcheckout_order_id', '=', txid)], limit=1)
        else:
            txid = self._get('tx', 0)
            values['tx'] = request.env['payment.transaction'].sudo().browse(txid)
        self._del()
        return request.render('payment_jetcheckout_system.page_result', values)

    @http.route(['/my/payment/transactions', '/my/payment/transactions/page/<int:page>'], type='http', auth='user', methods=['GET'], website=True)
    def page_system_payment_transaction(self, page=0, tpp=20, **kwargs):
        values = self._prepare()
        tx_ids = request.env['payment.transaction'].sudo().search([
            ('acquirer_id', '=', values['acquirer'].id),
            ('partner_id', '=', values['partner'].id)
        ])
        pager = request.website.pager(url='/my/payment/transactions', total=len(tx_ids), page=page, step=tpp, scope=7, url_args=kwargs)
        offset = pager['offset']
        txs = tx_ids[offset: offset + tpp]
        values.update({
            'pager': pager,
            'txs': txs,
            'tpp': tpp,
        })
        return request.render('payment_jetcheckout_system.page_transaction', values)

    @http.route(['/my/payment/query/partner'], type='json', auth='public', website=True)
    def page_system_payment_query_partner(self, **kwargs):
        partner = request.env['res.partner'].sudo().search([
            ('vat', '!=', False),
            ('vat', '=', kwargs.get('vat')),
            ('company_id', '=', request.env.company.id),
        ], limit=1)
        if not partner:
            return {
                'vat': '11111111111',
            }
        else:
            return partner.read([
                'id',
                'vat',
                'name',
                'phone',
                'email',
                'city',
                'street',
                'country_id',
                'state_id',
            ])[0]
        return {}

    @http.route(['/my/payment/create/partner'], type='json', auth='public', website=True)
    def page_system_payment_create_partner(self, **kwargs):
        if request.env.user.has_group('base.group_public'):
            return {'error': _('Only registered users can create partners.<br/>Please contact with your system administrator.')}

        company = request.env.company
        values = {**kwargs}
        values.update({
            'company_id': company.id,
            'system': company.system,
        })
        try:
            if not values.get('vat'):
                raise UserError(_('Please enter ID number'))
            else:
                partner = request.env['res.partner'].sudo().search([
                    ('vat', '!=', False),
                    ('vat', '=', values['vat']),
                    ('company_id', '=', company.id)
                ], limit=1)
                if partner:
                    raise UserError(_('There is already a partner with the same ID Number'))

            if not values.get('email'):
                email = company.email
                if not email or '@' not in email:
                    email = 'vat@paylox.io'
                name, domain = email.rsplit('@', 1)
                values['email'] = '%s@%s' % (values['vat'], domain)

            partner = request.env['res.partner'].sudo().with_context(no_vat_validation=True).create(values)
            return partner.read([value for value in kwargs.keys()])[0] or {}
        except UserError as e:
            return {'error': str(e)}
        except Exception as e:
            raise Exception(e)
