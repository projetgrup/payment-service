# -*- coding: utf-8 -*-
import requests
from pytz import timezone
from dateutil import parser
from datetime import datetime, timedelta
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.connector_syncops.models.config import DAYS


class Partner(models.Model):
    _inherit = 'res.partner'

    syncops_data = fields.Text(string='syncOPS Data')
    syncops_ok = fields.Boolean('syncOPS Ready', readonly=True)
    syncops_state = fields.Boolean('syncOPS State', readonly=True)
    syncops_ref = fields.Char('syncOPS Reference', readonly=True)
    syncops_state_message = fields.Text('syncOPS State Message', readonly=True)

    @api.model
    def cron_sync(self):
        self = self.sudo()
        now = datetime.now()
        tz = timezone('Europe/Istanbul')
        now += tz.utcoffset(now)
        pre = now - timedelta(hours=1)
        companies = self.env['res.company'].search([
            ('system', '!=', False),
            ('syncops_cron_sync_partner', '=', True),
            ('syncops_cron_sync_item_subtype', '!=', False),
        ])
        for company in companies:
            days = map(lambda d: DAYS[d], company.syncops_cron_sync_partner_day_ids.mapped('code'))
            if now.weekday() in days:
                hour = company.syncops_cron_sync_partner_hour % 24
                time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if pre < time <= now:
                    wizard = self.env['syncops.sync.wizard'].create({
                        'type': 'partner',
                        'system': company.system,
                    })
                    wizard.with_company(company.id).confirm()
                    wizard.with_company(company.id).with_context(wizard_id=wizard.id).sync()
                    wizard.unlink()

    def action_check_connector(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        connector = self.env['syncops.connector'].sudo()._find('payment_post_partner', company=company)
        if not connector:
            raise UserError(_('No syncOPS connector found'))

        if not self.id:
            raise UserError(_('Please save partner before checking connector logs'))

        result = []
        try:
            url = self.env['ir.config_parameter'].sudo().get_param('syncops.url')
            if not url:
                raise ValidationError(_('No syncOPS endpoint URL found'))

            url += '/api/v1/log'
            response = requests.get(url, params={
                'username': connector.username,
                'token': connector.token,
                'reference': str(self.id),
            })
            if response.status_code == 200:
                results = response.json()
                if not results.get('status') == 0:
                    raise UserError(results['message'])
                logs = results.get('logs', [])
                for log in logs:
                    result.append({
                        'connector_id': connector.id,
                        'company_id': self.env.company.id,
                        'date': parser.parse(log['date']),
                        'partner_name': log['partner'],
                        'connector_name': log['connector'],
                        'token_name': log['token'],
                        'method_name': log['method'],
                        'status': log['status'],
                        'state': log['state'],
                        'message': log['message'],
                        'request_data': log['request_data'],
                        'request_raw': log['request_raw'],
                        'request_method': log['request_method'],
                        'request_url': log['request_url'],
                        'response_code': log['response_code'],
                        'response_message': log['response_message'],
                        'response_data': log['response_data'],
                        'response_raw': log['response_raw'],
                    })
            else:
                raise UserError(response.text or response.reason)
        except Exception as e:
            raise UserError(str(e))

        if result:
            logs = self.env['syncops.log'].sudo().create(result)
            action = self.env.ref('connector_syncops.action_log').sudo().read()[0]
            action['context'] = {'create': False, 'delete': False, 'edit': False, 'import': False}
            action['domain'] = [('id', 'in', logs.ids)]
            return action
        else:
            raise UserError(_('No log found'))

    def action_process_connector(self):
        self.ensure_one()
        if not self.syncops_ok or not self.syncops_state:
            return

        params = {
            'email': self.email or '',
            'mobile': self.mobile or '',
            'city': self.state_id.name or '',
            'town': self.city or '',
            'address': self.street or '',
        }
        if self.is_company:
            params.update({
                'type': 0,
                'name': self.name,
                'vat': self.vat or '',
                'taxOffice': self.paylox_tax_office or '',
            })
        else:
            name, surname = self.name.rsplit(' ', 1)
            params.update({
                'type': 1,
                'name': name or '',
                'surname': surname or '',
                'vat': self.vat or '',
            })

        company = self.company_id or self.env.company
        result, message = self.env['syncops.connector'].sudo()._execute('payment_post_partner', reference=str(self.id), params=params, company=company, message=True)

        if result is None:
            self.write({
                'syncops_state': True,
                'syncops_state_message': _('This partner has not been successfully posted to connector.\n%s') % message
            })
        else:
            ref = result and result[0].get('ref') or False
            self.write({
                'ref': ref,
                'syncops_ref': ref,
                'syncops_state': False,
                'syncops_state_message': _('This partner has been successfully posted to connector.')
            })
        self.env.cr.commit()

    @api.model
    def create(self, values):
        connector = self.env['syncops.connector'].sudo()._find('payment_post_partner')
        if connector:
            values.update({
                'syncops_ok': True,
                'syncops_state': True,
            })
        res = super().create(values)
        if connector:
            res.action_process_connector()
        return res


class PartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.depends('api_state', 'api_message')
    def _compute_api_result(self):
        has_group_check_iban = self.env.user.has_group('payment_syncops.group_check_iban')
        for bank in self:
            company = bank.partner_id.company_id or self.env.company
            if company.syncops_check_iban and has_group_check_iban:
                if bank.syncops_api_state and bank.api_state:
                    bank.api_result = '<i class="fa fa-check text-primary" title="%s"/><i class="fa fa-check text-primary" title="" style="position:absolute;pointer-events:none;margin-top:1px;margin-left:-8px;"/>' % bank.api_message
                elif bank.syncops_api_state:
                    bank.api_result = '<i class="fa fa-check text-primary" title="%s"/>' % bank.api_message
                elif bank.api_message:
                    bank.api_result = '<i class="fa fa-times text-danger" title="%s"/>' % bank.api_message
                else:
                    bank.api_result = '<i class="fa fa-minus text-muted" title="%s"/>' % _('No message yet')
            else:
                if bank.api_state:
                    bank.api_result = '<i class="fa fa-check text-primary" title="%s"/>' % bank.api_message
                elif bank.api_message:
                    bank.api_result = '<i class="fa fa-times text-danger" title="%s"/>' % bank.api_message
                else:
                    bank.api_result = '<i class="fa fa-minus text-muted" title="%s"/>' % _('No message yet')

    syncops_api_state = fields.Boolean('syncOPS State')

    def _paylox_api_save(self, acquirer, method, data):
        user = self.env.user
        partner = self.partner_id
        company = partner.company_id or self.env.company
        if company.syncops_check_iban and not self.syncops_api_state and user.has_group('payment_syncops.group_check_iban'):
            iban = self.env['syncops.partner.iban'].sudo().search([('name', '=', data['iban'])])
            if not iban:
                result, message = self.env['syncops.connector'].sudo()._execute('other_get_ozan_iban', reference=str(self.id), params={
                    'vat': data['tax_number'],
                    'iban': data['iban'],
                }, company=self.env.company, message=True)
                if result is None:
                    self.write({'syncops_api_state': False})
                    return {'state': False, 'message': message}
                elif not result[0]['ok']:
                    self.write({'syncops_api_state': False})
                    return {'state': False, 'message': result[0]['message']}
                iban.create({'name': data['iban']})
        self.write({'syncops_api_state': True})
        return super()._paylox_api_save(acquirer, method, data)


class SyncopsPartnerIban(models.Model):
    _name = 'syncops.partner.iban'
    _description = 'syncOPS Partner Bank IBAN'

    name = fields.Char()
