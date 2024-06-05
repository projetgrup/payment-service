# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentPlanWizard(models.TransientModel):
    _inherit = 'payment.plan.wizard'

    method_supplier = fields.Selection([
        ('tx', 'Card Transaction Limit'),
        ('manual', 'Manual'),
    ], default='tx')

    def action_confirm(self):
        pass
