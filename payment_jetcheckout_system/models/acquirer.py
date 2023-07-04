# -*- coding: utf-8 -*-
from odoo import fields, models, api


class PaymentPayloxBranch(models.Model):
    _name = 'payment.acquirer.jetcheckout.branch'
    _description = 'Paylox Company Branches'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    acquirer_id = fields.Many2one('payment.acquirer')
    name = fields.Char(string='Branch Name', required=True)
    journal_id = fields.Many2one('payment.acquirer.jetcheckout.journal', string='Method')
    user_ids = fields.Many2many('res.users', 'jetcheckout_branch_user_rel', 'branch_id', 'user_id', string='Users')
    account_code = fields.Char(string='Account Code', required=True)
    company_id = fields.Many2one('res.company', ondelete='cascade', readonly=True)
    website_id = fields.Many2one('website', ondelete='cascade', readonly=True)


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    paylox_branch_ids = fields.One2many('payment.acquirer.jetcheckout.branch', 'acquirer_id', groups='base.group_user')
    jetcheckout_no_dashboard_button = fields.Boolean('Hide Dashboard Payment Button', groups='base.group_user')

    def _get_branch_line(self, name, user):
        line = self._get_journal_line(name)
        if line:
            domain = [('acquirer_id', '=', self.id), ('journal_id', '=', line.id)]

            branch = self.env['payment.acquirer.jetcheckout.branch'].search(domain + [('user_ids', 'in', [user.id])], limit=1)
            if branch:
                return branch

            branch = self.env['payment.acquirer.jetcheckout.branch'].search(domain + [('id', '=', user.acquirer_branch_id.id), ('user_ids', '=', False)], limit=1)
            if branch:
                return branch

            branch = self.env['payment.acquirer.jetcheckout.branch'].search(domain + [('user_ids', '=', False)], limit=1)
            if branch:
                return branch

        return None

    @api.model
    def has_dashboard_button(self):
        acquirer = self._get_acquirer(providers=['jetcheckout'], limit=1, raise_exception=False)
        if not acquirer:
            return False
        return not acquirer.jetcheckout_no_dashboard_button
