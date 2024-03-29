# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    paylox_contactless_apikey = fields.Char('Paylox Contactless API Key')
    paylox_contactless_secretkey = fields.Char('Paylox Contactless Secret Key')
    paylox_contactless_url = fields.Char('Paylox Contactless Deeplink URL')
