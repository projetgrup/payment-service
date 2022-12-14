# -*- coding: utf-8 -*-
from odoo import fields, models


class PaymentAcquirerJetcheckoutBranch(models.Model):
    _name = 'payment.acquirer.jetcheckout.branch'
    _description = 'Jetcheckout Company Branches'

    acquirer_id = fields.Many2one('payment.acquirer')
    name = fields.Char(string='Branch Name', required=True)
    journal_id = fields.Many2one('payment.acquirer.jetcheckout.journal', string='Method')
    user_ids = fields.Many2many('res.users', 'jetcheckout_branch_user_rel', 'branch_id', 'user_id', string='Users', required=True)
    account_code = fields.Char(string='Account Code', required=True)
    company_id = fields.Many2one('res.company', ondelete='cascade', readonly=True)
    website_id = fields.Many2one('website', ondelete='cascade', readonly=True)


class PaymentAcquirerJetcheckout(models.Model):
    _inherit = 'payment.acquirer'

    jetcheckout_branch_ids = fields.One2many('payment.acquirer.jetcheckout.branch', 'acquirer_id', groups='base.group_user')

    def _get_branch_line(self, name, user):
        line = self._get_journal_line(name)
        if line:
            return self.env['payment.acquirer.jetcheckout.branch'].search([
                ('acquirer_id', '=', self.id),
                ('journal_id', '=', line.id),
                ('user_ids', 'in', [user.id])
            ], limit=1)
        return None
