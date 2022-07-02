# -*- coding: utf-8 -*-
import pymssql
from pymssql._pymssql import OperationalError

from odoo import models, _
from odoo.exceptions import UserError


class IrConnector(models.Model):
    _inherit = 'ir.connector'

    def _test_database_mssql_connection(self):
        try:
            pymssql.connect(self.server, self.username, self.password, self.database)
        except OperationalError as e:
            raise UserError(_('Connection failed. Please check database settings. (%s)') % e)
        except:
            raise UserError(_('Connection failed. Please check database settings.'))

    def _execute_database_mssql_query(self, procedure, parameters):
        try:
            params = []
            for key, value in parameters.items():
                params.append('@%s = %s' % (key, value))

            conn = pymssql.connect(self.server, self.username, self.password, self.database)
            cursor = conn.cursor(as_dict=True)
            cursor.execute(f"""EXEC {procedure} {', '.join(params)}""")
            result = cursor.fetchall()
            conn.close()
            return result
        except OperationalError as e:
            raise UserError(_('Query failed. (%s)') % e)
        except:
            raise UserError(_('Query failed. Please check your query structure.'))
