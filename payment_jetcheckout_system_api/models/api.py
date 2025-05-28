# -*- coding: utf-8 -*-

from odoo import fields, models


class PaymentPayloxAPI(models.Model):
    _inherit = 'payment.acquirer.jetcheckout.api'

    perm_audit = fields.Boolean(string='Allow Audit Services')
