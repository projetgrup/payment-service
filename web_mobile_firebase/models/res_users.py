# -*- coding: utf-8 -*-

from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    firebase_token_ids = fields.One2many('res.users.token', 'user_id', string='Firebase Tokens', readonly=True)


class ResUsersToken(models.Model):
    _name = 'res.users.token'
    _description = 'Users Firebase Tokens'

    user_id = fields.Many2one('res.users')
    name = fields.Char('Device', readonly=True)
    token = fields.Char('Token', readonly=True)

