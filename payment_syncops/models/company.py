# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date


class ResCompany(models.Model):
    _inherit = 'res.company'

    syncops_sync_item_subtype = fields.Char()
