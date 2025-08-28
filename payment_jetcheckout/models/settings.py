# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.depends('company_id')
    def _compute_payment_log_opt(self):
        for settings in self:
            settings.payment_log_opt = self.env['ir.config_parameter'].get_param('paylox.log') == 'opt'

    payment_log = fields.Selection([
        ('no', 'Do not save'),
        ('opt', 'Optional per company'),
        ('all', 'Save for all'),
    ], string='Enable Logging for Paylox Requests', config_parameter='paylox.log')
    payment_log_ok = fields.Boolean(related='company_id.payment_log_ok', readonly=False)
    payment_log_opt = fields.Boolean(string='Optional Logging for Payment Requests', compute='_compute_payment_log_opt', compute_sudo=True)

    installment_show_monthly = fields.Boolean(
        string='Show Monthly Price Column on Installments',
        config_parameter='paylox.installment.show_monthly',
        default=True,
    )
