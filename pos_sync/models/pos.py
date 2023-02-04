# -*- coding: utf-8 -*-
from odoo import models, fields


class PosSync(models.Model):
    _name = 'pos.sync'
    _description = 'Point of Sale - Sync'

    name = fields.Char()
    data = fields.Text()
    cashier_id = fields.Integer()
    session_id = fields.Many2one('pos.session')

class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_close(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        res = super().action_pos_session_close(balancing_account=balancing_account, amount_to_balance=amount_to_balance, bank_payment_method_diffs=bank_payment_method_diffs)
        self.env['pos.sync'].sudo().search([('session_id', '=', self.id)]).unlink()
        return res
