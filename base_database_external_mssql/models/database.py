# -*- coding: utf-8 -*-
import pymssql
from pymssql._pymssql import OperationalError

from odoo import models, fields, _
from odoo.exceptions import UserError

class IrDatabaseExternal(models.Model):
    _inherit = 'ir.database.external'

    type = fields.Selection(selection_add=[('mssql', 'Microsoft SQL')])

    def _test_mssql_connection(self):
        try:
            pymssql.connect(self.server, self.username, self.password, self.database)
        except OperationalError as e:
            raise UserError(_('Connection failed. Please check database settings. (%s)') % e)
        except:
            raise UserError(_('Connection failed. Please check database settings.'))
