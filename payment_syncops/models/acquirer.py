# -*- coding: utf-8 -*-
from odoo import fields, models


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    syncops_excluded_state_ids = fields.Many2many('ir.model.fields.selection', 'acquirer_syncops_excluded_state_rel', 'acquirer_id', 'state_id', groups='base.group_user', domain='[("field_id.name", "=", "state"), ("field_id.model", "=", "payment.transaction")]')
