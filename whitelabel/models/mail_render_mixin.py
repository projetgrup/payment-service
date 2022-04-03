# -- coding: utf-8 --
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

import re
from lxml import etree, html
from odoo import api, models


class MailRenderMixin(models.AbstractModel):
    _inherit = 'mail.render.mixin'

    def branding_links(self, value, remove_parent=True, remove_before=False, to_keep=None):
        if len(value) < 20:
            return value
        if type(value) is bytes:
            value = value.decode()
        has_link = re.search(r'<a\s(.*)odoo\.com', value, flags=re.IGNORECASE)
        if has_link:
            if to_keep:
                to_change = value.split(to_keep)
            else:
                to_change = [value]
                to_keep = ""
            new_parts = []
            for part in to_change:
                tree = html.fromstring(part)
                if tree is None:
                    new_parts.append(part)
                    continue
                odoo_anchors = tree.xpath('//a[contains(@href,"odoo.com")]')
                for elem in odoo_anchors:
                    parent = elem.getparent()
                    previous = elem.getprevious()

                    if remove_before and not remove_parent and previous is not None:
                        previous.tail = ''
                    if remove_parent and len(parent.getparent()):
                        parent.getparent().remove(parent)
                    else:
                        if parent.tag == 'td':
                            parent.getparent().remove(parent)
                        else:
                            parent.remove(elem)
                part = etree.tostring(
                    tree, pretty_print=True, method='html', encoding='unicode'
                )
                new_parts.append(part)
            value = str(to_keep).join(new_parts)
        return value

    @api.model
    def _render_template(self, template_src, model, res_ids, engine='inline_template', add_context=None, options=None, post_process=False):
        res = super()._render_template(template_src, model, res_ids, engine=engine, add_context=add_context, options=options, post_process=post_process)
        for key in res_ids:
            res[key] = self.branding_links(res[key])
        return res
