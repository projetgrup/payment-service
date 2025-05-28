# -*- coding: utf-8 -*-
from . import company
from . import report

import logging
from odoo.http import request, root

_logger = logging.getLogger(__name__)

try:
    import xlwt

    class PatchedWorkbook(xlwt.Workbook):

        def add_sheet(self, name, cell_overwrite_ok=False):
            res = super(PatchedWorkbook, self).add_sheet(name, cell_overwrite_ok=cell_overwrite_ok)
            cids = request.httprequest.cookies.get('cids')
            if cids:
                cid = cids.split(',', 1)[0]
                company = request.env['res.company'].sudo().browse(int(cid))
                if company.sec_dlp_ok:
                    res.write(1040000, 1040000, company.get_dlp_tag())
            return res

    xlwt.Workbook = PatchedWorkbook

except:
    _logger.error('An error occured when patching xlwt', exc_info=True)

try:
    import xlsxwriter

    class PatchedXlsxWorkbook(xlsxwriter.Workbook):

        def add_worksheet(self, name=None, **kw):
            res = super(PatchedXlsxWorkbook, self).add_worksheet(name, **kw)
            try:
                cids = request.httprequest.cookies.get('cids')
                sid = request.httprequest.cookies.get('session_id')
                uid = root.session_store.get(sid)['uid']
            except:
                cids, uid = None, None
            if cids:
                cid = cids.split(',', 1)[0]
                company = request.env['res.company'].sudo().browse(int(cid))
                if company.sec_dlp_ok:
                    formatter = self.add_format({'num_format': ';;;', 'font_color': '#FFFFFF'})
                    res.write('XEV1040000', company.get_dlp_tag(), formatter)
                    res.set_row(1039999, None, None, {'hidden': True})
                    res.set_column('XEV:XEV', None, None, {'hidden': True})
                    if uid:
                        user = request.env['res.users'].sudo().browse(int(uid))
                        if user:
                            res.write('XEW1040000', user.email or user.login or '', formatter)
                            res.set_column('XEW:XEW', None, None, {'hidden': True})
            return res

    xlsxwriter.Workbook = PatchedXlsxWorkbook

except:
    _logger.error('An error occured when patching xlsxwriter', exc_info=True)
