# -- coding: utf-8 --
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

from odoo import models


class MailMail(models.AbstractModel):
    _inherit = "mail.mail"

    def _send_prepare_body(self):
        body_html = super()._send_prepare_body()
        return self.env["mail.render.mixin"].remove_href_odoo(
            body_html or "", remove_parent=0, remove_before=1, to_keep=self.body
        )
