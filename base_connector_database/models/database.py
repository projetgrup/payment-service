# -*- coding: utf-8 -*-
from odoo import models, fields


class IrConnector(models.Model):
    _inherit = 'ir.connector'

    type = fields.Selection(selection_add=[('database', 'Database')], ondelete={'database': 'cascade'})
    database = fields.Char()


class IrConnectorSubtype(models.Model):
    _inherit = 'ir.connector.subtype'

    type = fields.Selection(selection_add=[('database', 'Database')], ondelete={'database': 'cascade'})
