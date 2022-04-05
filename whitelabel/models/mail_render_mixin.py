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

    def remove_href_odoo(
            self, value, remove_parent=True, remove_before=False, to_keep=None
    ):
        if len(value) < 20:
            return value
        # value can be bytes type; ensure we get a proper string
        if type(value) is bytes:
            value = value.decode()
        has_odoo_link = re.search(r"<a\s(.*)odoo\.com", value, flags=re.IGNORECASE)
        if has_odoo_link:
            # We don't want to change what was explicitly added in the message body,
            # so we will only change what is before and after it.
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
                        # remove 'using' that is before <a and after </span>
                        previous.tail = ""
                    if remove_parent and len(parent.getparent()):
                        # anchor <a href odoo has a parent powered by that must be removed
                        parent.getparent().remove(parent)
                    else:
                        if parent.tag == "td":  # also here can be powered by
                            parent.getparent().remove(parent)
                        else:
                            parent.remove(elem)
                part = etree.tostring(
                    tree, pretty_print=True, method="html", encoding="unicode"
                )
                new_parts.append(part)
            value = str(to_keep).join(new_parts)
        return value

    @api.model
    def _render_template(
            self,
            template_src,
            model,
            res_ids,
            engine="qweb_view",
            add_context=None,
            options=None,
            post_process=False,
    ):
        """replace anything that is with odoo in templates
        if is a <a that contains odoo will delete it completely
        original:
         Render the given string on records designed by model / res_ids using
        the given rendering engine.
        :param str template_src: template text to render (jinja) or  (qweb)
          this could be cleaned but hey, we are in a rush
        :param str model: model name of records on which we want to perform rendering
        :param list res_ids: list of ids of records (all belonging to same model)
        :param string engine: jinja
        :param post_process: perform rendered str / html post processing (see
          ``_render_template_postprocess``)
        :return dict: {res_id: string of rendered template based on record}"""
        orginal_rendered = super()._render_template(
            template_src,
            model,
            res_ids,
            engine=engine,
            add_context=add_context,
            post_process=post_process,
        )

        for key in res_ids:
            orginal_rendered[key] = self.remove_href_odoo(orginal_rendered[key])

        return orginal_rendered

    def _replace_local_links(self, html, base_url=None):
        message = super()._replace_local_links(html)
        message = re.sub(
            r"""(Powered by\s(.*)Odoo</a>)""", "<div>&nbsp;</div>", message
        )
        return message