# -*- coding: utf-8 -*-
from odoo import models, api


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
