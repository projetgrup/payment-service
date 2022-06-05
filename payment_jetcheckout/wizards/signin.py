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
    gateway_api = fields.Char('API URL')
    gateway_app = fields.Char('Gateway URL')
    gateway_database = fields.Char('Database Name')

    def signin(self):
        api = self.gateway_api
        if api and api[-1] == '/':
            api = api[:-1]

        url = self.gateway_app
        if url and url[-1] == '/':
            url = url[:-1]
        url = url and '%s/jsonrpc' % url or 'https://app.jetcheckout.com/jsonrpc'
        database = self.gateway_database or 'jetcheckout'
        uid = rpc.login(url, database, self.username, self.password)
        if not uid:
            raise ValidationError(_('Connection is failed. Please correct your username or password.'))

        vals = {
            'jetcheckout_username': self.username,
            'jetcheckout_password': self.password,
            'jetcheckout_user_id': uid,
        }

        if self.option:
            if api:
                vals.update({'jetcheckout_gateway_api': api})
            if url:
                vals.update({'jetcheckout_gateway_app': url})
            if database:
                vals.update({'jetcheckout_gateway_database': database})

        self.acquirer_id.write(vals)
        return self.acquirer_id.action_jetcheckout_application()
