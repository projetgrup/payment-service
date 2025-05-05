# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    user_template_id = fields.Many2one('res.users', string='User Template')
    auth_unauthorized_action = fields.Selection([
        ('create', 'Create User'),
        ('deny', 'Deny User'),
    ], string='Action to Unauthorized User')
