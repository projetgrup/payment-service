# -*- coding: utf-8 -*-
from odoo import models, fields

class Website(models.Model):
    _inherit = 'website'

    payment_footer = fields.Html('Footer')
    payment_privacy_policy = fields.Html('Privacy Policy')
    payment_sale_agreement = fields.Html('Sale Agreement')
    payment_membership_agreement = fields.Html('Membership Agreement')
    payment_contact_page = fields.Html('Contact Page')
