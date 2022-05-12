# -*- coding: utf-8 -*-
import json
import random
import urllib.request

from odoo import fields, models, _
from odoo.exceptions import ValidationError
from ..models.rpc import rpc

class PaymentAcquirerJetcheckoutSignin(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.signin'
    _description = 'Jetcheckout Signin'

    acquirer_id = fields.Many2one('payment.acquirer')
    username = fields.Char('Username')
    password = fields.Char('Password')

    def signin(self):
        uid = rpc.login(self.username, self.password)
        if not uid:
            raise ValidationError(_('Connection is failed. Please correct your username or password.'))

        self.acquirer_id.jetcheckout_username = self.username
        self.acquirer_id.jetcheckout_password = self.password
        self.acquirer_id.jetcheckout_userid = uid
        return self.acquirer_id.action_jetcheckout_application()
