# -*- coding: utf-8 -*-

from odoo import models, fields


class WebMobileRoute(models.Model):
    _name = 'web.mobile.route'
    _description = 'Web Mobile Routes'

    name = fields.Char()
    address_ids = fields.One2many('web.mobile.route.address')


class WebMobileRouteAddress(models.Model):
    _name = 'web.mobile.route.address'
    _description = 'Web Mobile Route Addresses'

    name = fields.Char()
