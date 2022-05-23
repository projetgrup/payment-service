# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError

class Company(models.Model):
    _inherit = 'res.company'

    def action_website_setting(self):
        self.ensure_one()
        action = self.env.ref('website.action_website_list').sudo().read()[0]
        action['domain'] = [('company_id', '=', self.id)]
        return action

    def action_company_details(self):
        self.ensure_one()
        action = self.env.ref('base.action_res_company_form').sudo().read()[0]
        action['res_id'] = self.id
        action['views'] = [(False, 'form')]
        return action

    def action_users(self):
        self.ensure_one()
        action = self.env.ref('base.action_res_users').sudo().read()[0]
        action['domain'] = [('company_id', '=', self.id)]
        return action

    def action_pos_setting(self):
        self.ensure_one()
        action = self.env.ref('payment_student.action_acquirer').sudo().read()[0]
        action['domain'] = [('company_id', '=', self.id)]
        return action

    def action_jconda_integration(self):
        raise UserError(_('Coming soon...'))
