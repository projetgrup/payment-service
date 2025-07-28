# -*- coding: utf-8 -*-

from odoo import models, fields


class WebMobileRoute(models.Model):
    _name = 'web.mobile.route'
    _description = 'Web Mobile Routes'

    token = fields.Char()
    url_ids = fields.One2many('web.mobile.route.url', 'route_id')


class WebMobileRouteUrl(models.Model):
    _name = 'web.mobile.route.url'
    _description = 'Web Mobile Route URLs'

    url = fields.Char()
    route_id = fields.Many2one('web.mobile.route', ondelete='cascade')
