# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields


class PosSync(models.Model):
    _name = 'pos.sync'
    _description = 'Point of Sale - Sync'

    name = fields.Char()
    data = fields.Text()
    cashier = fields.Integer()
    session = fields.Integer()

class PosConfig(models.Model):
    _inherit = 'pos.config'

    def _compute_sync_concurrent(self):
        concurrent = odoo.multi_process or odoo.evented
        for config in self:
            config.sync_concurrent_readonly = not concurrent
            config.sync_concurrent = concurrent and config.sync_concurrent_ok

    def _set_sync_concurrent(self):
        for config in self:
            config.sync_concurrent_ok = config.sync_concurrent

    sync_ok = fields.Boolean('Synchronization')
    sync_concurrent_readonly = fields.Boolean('Synchronization Concurrent Readonly', compute='_compute_sync_concurrent')
    sync_concurrent_ok = fields.Boolean('Synchronization Concurrent')
    sync_concurrent = fields.Boolean('Is Synchronization Concurrent', compute='_compute_sync_concurrent', inverse='_set_sync_concurrent')
    sync_interval = fields.Integer('Synchronization Interval', default=5)

class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_close(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        res = super().action_pos_session_close(balancing_account=balancing_account, amount_to_balance=amount_to_balance, bank_payment_method_diffs=bank_payment_method_diffs)
        self.env['pos.sync'].sudo().search([('session', '=', self.id)]).unlink()
        return res
