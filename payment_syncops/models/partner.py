# -*- coding: utf-8 -*-
from odoo import models, api, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    def _compute_field_bank_ids_api(self):
        user = self.env.user
        for partner in self:
            company = partner.company_id or self.env.company
            partner.field_bank_ids_api = company.syncops_check_iban and user.has_group('payment_syncops.group_check_iban')

    @api.model
    def cron_sync(self):
        self = self.sudo()
        for company in self.env['res.company'].search([('system', '!=', False)]):
            if company.syncops_cron_sync_partner:
                wizard = self.env['syncops.sync.wizard'].create({
                    'type': 'partner',
                    'system': company.system,
                })
                wizard.with_company(company.id).confirm()
                wizard.with_company(company.id).with_context(wizard_id=wizard.id).sync()
                wizard.unlink()


class PartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def _paylox_api_save(self, acquirer, method, data):
        if self.partner_id.field_bank_ids_api:
            iban = self.env['syncops.partner.iban'].sudo().search([('name', '=', data['iban'])])
            if not iban:
                result, message = self.env['syncops.connector'].sudo()._execute('other_get_ozan_iban', reference=str(self.id), params={
                    'vat': data['tax_number'],
                    'iban': data['iban'],
                }, company=self.env.company, message=True)
                if result is None:
                    return {'state': False, 'message': message}
                elif not result[0]['ok']:
                    return {'state': False, 'message': result[0]['message']}
                iban.create({'name': data['iban']})
        else:
            return {'state': False, 'message': False}

        return super()._paylox_api_save(acquirer, method, data)


class SyncopsPartnerIban(models.Model):
    _name = 'syncops.partner.iban'
    _description = 'syncOPS Partner Bank IBAN'

    name = fields.Char()
