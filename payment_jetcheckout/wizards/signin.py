# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from ..models.rpc import rpc

class PaymentAcquirerJetcheckoutSignin(models.TransientModel):
    _name = 'payment.acquirer.jetcheckout.signin'
    _description = 'Jetcheckout Signin'

    acquirer_id = fields.Many2one('payment.acquirer')
    username = fields.Char('Username')
    password = fields.Char('Password')
    option = fields.Boolean('Advanced Options')
    gateway_url = fields.Char('Gateway URL')
    gateway_app = fields.Char('Application URL')
    gateway_database = fields.Char('Database Name')

    def signin(self):
        url = self.gateway_app and '%s/jsonrpc' % self.gateway_app or 'https://app.jetcheckout.com/jsonrpc'
        database = self.gateway_database or 'jetcheckout'
        uid = rpc.login(url, database, self.username, self.password)
        if not uid:
            raise ValidationError(_('Connection is failed. Please correct your username or password.'))

        vals = {
            'jetcheckout_username': self.username,
            'jetcheckout_password': self.password,
            'jetcheckout_userid': uid,
        }

        if self.option:
            if self.gateway_url:
                vals.update({'jetcheckout_gateway_url': self.gateway_url})
            if self.gateway_app:
                vals.update({'jetcheckout_gateway_app': url})
            if self.gateway_database:
                vals.update({'jetcheckout_gateway_database': database})

        self.acquirer_id.write(vals)
        return self.acquirer_id.action_jetcheckout_application()
