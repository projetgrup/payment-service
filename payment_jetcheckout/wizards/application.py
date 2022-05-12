# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError

class PaymentAcquirerJetcheckoutApiApplication(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.application'
    _description = 'Jetcheckout Application'

    acquirer_id = fields.Many2one('payment.acquirer')
    parent_id = fields.Many2one('payment.acquirer.jetcheckout.api.applications')
    pos_ids = fields.Many2many('payment.acquirer.jetcheckout.api.pos', 'payment_jetcheckout_api_application_pos_rel', 'application_id', 'pos_id', string='Poses', ondelete='cascade')
    res_id = fields.Integer(readonly=True)
    name = fields.Char('Name')
    application_id = fields.Char('Application ID', readonly=True)
    secret_key = fields.Char('Secret Key', readonly=True)
    is_active = fields.Boolean('Active', default=True)
    first_selection = fields.Selection([
        ('CardBank', 'Card Bank'),
        ('LowCostRate', 'Low Cost Rate'),
        ('Priority', 'Priority'),
    ], string='First Selection Criteria')
    second_selection = fields.Selection([
        ('CardBank', 'Card Bank'),
        ('LowCostRate', 'Low Cost Rate'),
        ('Priority', 'Priority'),
    ], string='Second Selection Criteria')
    third_selection = fields.Selection([
        ('CardBank', 'Card Bank'),
        ('LowCostRate', 'Low Cost Rate'),
        ('Priority', 'Priority'),
    ], string='Third Selection Criteria')
    virtual_poses = fields.Char('Virtual Pos', readonly=True)

    def setup(self):
        values = {
            'name': self.name,
            'is_active': self.is_active,
            'user_id': self.acquirer_id.jetcheckout_userid,
        }
        self.acquirer_id._rpc('jet.application', 'create', values)

    def select(self):
        if not self.is_active:
            raise UserError(_('Please activate this record before selecting it'))

        self.acquirer_id.jetcheckout_api_name = self.name
        self.acquirer_id.jetcheckout_api_key = self.application_id
        self.acquirer_id.jetcheckout_secret_key = self.secret_key

        self.acquirer_id.jetcheckout_journal_ids = [(5, 0, 0)] + [(0, 0, {
            'provider_id': pos.provider_id.id,
            'pos_id': self.env['payment.acquirer.jetcheckout.pos'].search([('name','=',pos.name)], limit=1).id,
            'company_id': self.acquirer_id.company_id.id,
            'website_id': self.acquirer_id.website_id.id
        }) for pos in self.pos_ids.filtered(lambda x: x.is_active)]

    def write(self, vals):
        values = {key: vals[key] for key in (
            'name',
            'is_active',
            'first_selection',
            'second_selection',
            'third_selection'
        ) if key in vals}
        if 'first_selection' in values:
            values['first_selection'] = values['first_selection'].replace(' ')
        if 'second_selection' in values:
            values['second_selection'] = values['second_selection'].replace(' ')
        if 'third_selection' in values:
            values['third_selection'] = values['third_selection'].replace(' ')

        if values:
            self.acquirer_id._rpc('jet.application', 'write', self.res_id, values)

        res = super().write(vals)
        if 'name' in vals and self.acquirer_id.jetcheckout_api_key == self.application_id:
            self.acquirer_id.jetcheckout_api_name = self.name
        return res

class PaymentAcquirerJetcheckoutApiApplications(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.api.applications'
    _description = 'Jetcheckout Applications'

    acquirer_id = fields.Many2one('payment.acquirer')
    application_ids = fields.One2many('payment.acquirer.jetcheckout.api.application', 'parent_id', 'Applications')

