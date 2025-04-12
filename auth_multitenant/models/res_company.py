# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    user_template_id = fields.Many2one('res.users', string='User Template')
