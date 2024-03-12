# -*- coding: utf-8 -*-
import datetime
from collections import OrderedDict
from werkzeug.exceptions import NotFound
from dateutil.relativedelta import relativedelta

from odoo import http
from odoo.http import request
from odoo.tools.translate import _

from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import get_records_pager, pager as portal_pager


class CustomerPortal(portal.CustomerPortal):

    def _get_subscription_domain(self, partner):
        return [
            ('partner_id.id', 'in', [partner.id, partner.commercial_partner_id.id]),
        ]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'subscription_count' in counters:
            partner = request.env.user.partner_id
            values['subscription_count'] = (
                request.env['payment.subscription'].search_count(self._get_subscription_domain(partner))
                if request.env['payment.subscription'].check_access_rights('read', raise_exception=False)
                else 0
            )
        return values

    @http.route(['/my/subscriptions', '/my/subscriptions/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_subscriptions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        subscription = request.env['payment.subscription']
        domain = self._get_subscription_domain(partner)

        archive_groups = self._get_archive_groups('payment.subscription', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'}
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'open': {'label': _('In Progress'), 'domain': [('in_progress', '=', True)]},
            'pending': {'label': _('To Renew'), 'domain': [('to_renew', '=', True)]},
            'close': {'label': _('Closed'), 'domain': [('in_progress', '=', False)]},
        }

        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        account_count = subscription.sudo().search_count(domain)
        pager = portal_pager(
            url='/my/subscriptions',
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=account_count,
            page=page,
            step=self._items_per_page
        )
        accounts = subscription.sudo().search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_payment_subscriptions_history'] = accounts.ids[:100]

        values.update({
            'pager': pager,
            'accounts': accounts,
            'page_name': 'payment_subscription',
            'archive_groups': archive_groups,
            'default_url': '/my/subscriptions',
            'sortby': sortby,
            'filterby': filterby,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
        })
        return request.render('payment_subscription.portal_my_subscriptions', values)


class PaymentSubscription(http.Controller):

    @http.route([
        '/my/subscriptions/<int:account_id>/',
        '/my/subscriptions/<int:account_id>/<string:uuid>'
    ], type='http', auth='public', website=True)
    def subscription(self, account_id, uuid='', message='', message_class='', **kw):
        subscriptions = request.env['payment.subscription']
        if uuid:
            account = subscriptions.sudo().browse(account_id)
            if uuid != account.uuid:
                raise NotFound()
            if request.uid == account.partner_id.user_id.id:
                account = subscriptions.browse(account_id)
        else:
            account = subscriptions.browse(account_id)

        acquirers = request.env['payment.acquirer'].sudo()._get_compatible_acquirers(
            subscriptions.company_id.id,
            subscriptions.partner_id.id,
            currency_id=subscriptions.currency_id.id,
            force_tokenization=True,
            is_validation=not subscriptions.to_renew,
        )

        acc_pm = account.payment_token_id
        part_pms = account.partner_id.payment_token_ids.filtered(lambda pms: pms.acquirer_id.company_id == account.company_id)
        display_close = account.template_id.sudo().user_closable and account.in_progress
        is_follower = request.env.user.partner_id.id in [follower.partner_id.id for follower in account.message_follower_ids]
        active_plan = account.template_id.sudo()
        periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
        if account.recurring_rule_type != 'weekly':
            rel_period = relativedelta(datetime.datetime.today(), account.recurring_next_date)
            missing_periods = getattr(rel_period, periods[account.recurring_rule_type]) + 1
        else:
            delta = datetime.date.today() - account.recurring_next_date
            missing_periods = delta.days / 7

        action = request.env.ref('payment_subscription.action_payment_subscription')
        values = {
            'account': account,
            'template': account.template_id.sudo(),
            'display_close': display_close,
            'is_follower': is_follower,
            'reasons': request.env['payment.subscription.reason'].search([]),
            'missing_periods': missing_periods,
            'payment_mode': active_plan.payment_mode,
            'user': request.env.user,
            'acquirers': list(acquirers),
            'acc_pm': acc_pm,
            'part_pms': part_pms,
            'action': action,
            'message': message,
            'message_class': message_class,
            'change_pm': kw.get('change_pm') != None,
            'pricelist': account.pricelist_id.sudo(),
            'submit_class':'btn btn-primary mb8 mt8 float-right',
            'submit_txt':'Pay Subscription',
            'bootstrap_formatting':True,
            'return_url':'/my/subscriptions/' + str(account_id) + '/' + str(uuid),
            'is_salesman': request.env['res.users'].with_user(request.uid).has_group('sales_team.group_sale_salesman'),
        }

        history = request.session.get('my_subscriptions_history', [])
        values.update(get_records_pager(history, account))

        fees_by_acquirer = {
            acquirer: acquirer._compute_fees(
                account.recurring_total_incl,
                account.currency_id,
                account.partner_id.country_id
            ) for acquirer in acquirers.filtered('fees_active')
        }

        values['acq_extra_fees'] = fees_by_acquirer
        return request.render('payment_subscription.subscription', values)

    payment_succes_msg = 'message=Thank you, your payment has been validated.&message_class=alert-success'
    payment_fail_msg = 'message=There was an error with your payment, please try with another payment method or contact us.&message_class=alert-danger'

    @http.route([
        '/my/subscriptions/payment/<int:account_id>/',
        '/my/subscriptions/payment/<int:account_id>/<string:uuid>'
    ], type='http', auth='public', methods=['POST'], website=True)
    def payment(self, account_id, uuid=None, **kw):
        subscriptions = request.env['payment.subscription']
        invoice_res = request.env['account.move']
        get_param = ''
        if uuid:
            account = subscriptions.sudo().browse(account_id)
            if uuid != account.uuid:
                raise NotFound()
        else:
            account = subscriptions.browse(account_id)

        if int(kw.get('pm_id', 0)) > 0:
            account.payment_token_id = int(kw['pm_id'])

        if len(account.payment_token_id) == 0:
            get_param = 'message=No payment method have been selected for this subscription.&message_class=alert-danger'
            return request.redirect('/my/subscriptions/%s/%s?%s' % (account.id, account.uuid, get_param))

        payment_token = account.payment_token_id
        if payment_token:
            invoice_values = account.sudo()._prepare_invoice()
            new_invoice = invoice_res.sudo().create(invoice_values)
            tx = account.sudo().with_context(off_session=False)._do_payment(payment_token, new_invoice)[0]
            if tx.html_3ds:
                return tx.html_3ds

            get_param = self.payment_succes_msg if tx.payment_renewal_allowed else self.payment_fail_msg
            if tx.payment_renewal_allowed:
                account.send_success_mail(tx, new_invoice)
                msg_body = 'Manual payment succeeded. Payment reference: <a href=# data-oe-model=payment.transaction data-oe-id=%d>%s</a>; Amount: %s. Invoice <a href=# data-oe-model=account.move data-oe-id=%d>View Invoice</a>.' % (tx.id, tx.reference, tx.amount, new_invoice.id)
                account.message_post(body=msg_body)
            elif tx.state != 'pending':
                new_invoice.unlink()

        return request.redirect('/payment/process')

    @http.route([
        '/my/subscriptions/<sub_uuid>/payment/<int:tx_id>/accept/',
        '/my/subscriptions/<sub_uuid>/payment/<int:tx_id>/decline/',
        '/my/subscriptions/<sub_uuid>/payment/<int:tx_id>/exception/'
    ], type='http', auth='public', website=True)
    def payment_accept(self, sub_uuid, tx_id, **kw):
        subscriptions = request.env['payment.subscription']
        tx_res = request.env['payment.transaction']
        subscription = subscriptions.sudo().search([('uuid', '=', sub_uuid)])
        tx = tx_res.sudo().browse(tx_id)
        tx._handle_feedback_data(tx.acquirer_id.provider, kw)
        get_param = self.payment_succes_msg if tx.payment_renewal_allowed else self.payment_fail_msg
        return request.redirect('/my/subscriptions/%s/%s?%s' % (subscription.id, sub_uuid, get_param))

    @http.route(['/my/subscriptions/<int:subscription_id>/close'], type='http', methods=['POST'], auth='public', website=True)
    def close_account(self, subscription_id, uuid=None, **kw):
        subscriptions = request.env['payment.subscription']

        if uuid:
            subscription = subscriptions.sudo().browse(subscription_id)
            if uuid != subscription.uuid:
                raise NotFound()
        else:
            subscription = subscriptions.browse(subscription_id)

        if subscription.sudo().template_id.user_closable:
            subscription.reason_id = request.env['payment.subscription.reason'].browse(int(kw.get('reason_id')))
            if kw.get('closing_text'):
                subscription.message_post(body=_('Closing text : ') + kw.get('closing_text'))
            subscription.set_close()
            subscription.date = datetime.date.today().strftime('%Y-%m-%d')
        return request.redirect('/my/home')

    @http.route([
        '/my/subscriptions/<int:subscription_id>/set_pm',
        '/my/subscriptions/<int:subscription_id>/<string:uuid>/set_pm'
    ], type='http', methods=['POST'], auth='public', website=True)
    def set_payment_method(self, subscription_id, uuid=None, **kw):
        subscriptions = request.env['payment.subscription']
        if uuid:
            subscription = subscriptions.sudo().browse(subscription_id)
            if uuid != subscription.uuid:
                raise NotFound()
        else:
            subscription = subscriptions.browse(subscription_id)

        if kw.get('pm_id'):
            new_token = request.env['payment.token'].browse(int(kw.get('pm_id')))
            subscription.payment_token_id = new_token
            get_param = 'message=Your payment method has been changed for this subscription.&message_class=alert-success'
        else:
            get_param = 'message=Impossible to change your payment method for this subscription.&message_class=alert-danger'

        return request.redirect('/my/subscriptions/%s/%s?%s' % (subscription.id, subscription.uuid, get_param))
