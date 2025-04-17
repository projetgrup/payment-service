# -*- coding: utf-8 -*-
from . import company

import logging
from odoo import models, api
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _run_wkhtmltopdf(
            self,
            bodies,
            header=None,
            footer=None,
            landscape=False,
            specific_paperformat_args=None,
            set_viewport_size=False):
        try:
            dlptag = self.env.company.get_dlp_tag()
            bodies[-1] += f'<div style="display:none">{dlptag}</div>'
        except:
            pass
        return super(IrActionsReport, self)._run_wkhtmltopdf(
            bodies,
            header=header,
            footer=footer,
            landscape=landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size
        )

try:
    import xlwt

    class PatchedWorkbook(xlwt.Workbook):

        def save(self, filename_or_stream):
            try:
                dlptag = request.env.company.get_dlp_tag()
                dlpsheet = self.add_sheet()
                dlpsheet.write(0, 0, dlptag)
            except:
                pass
            return super(PatchedWorkbook, self).save(filename_or_stream)

    xlwt.Workbook = PatchedWorkbook

except:
    _logger.error('An error occured when patching xlwt', exc_info=True)

try:
    import xlsxwriter

    class PatchedXlsxWorkbook(xlsxwriter.Workbook):

        def close(self):
            try:
                dlptag = request.env.company.get_dlp_tag()
                dlpsheet = self.add_worksheet()
                dlpsheet.hide()
                dlpsheet.write('A1', dlptag)
            except:
                pass
            return super(PatchedXlsxWorkbook, self).close()

    xlsxwriter.Workbook = PatchedXlsxWorkbook

except:
    _logger.error('An error occured when patching xlsxwriter', exc_info=True)
