# -- coding: utf-8 --
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    whitelabel_favicon = fields.Binary(string="Whitelabel Favicon Image")
    title_brand = fields.Char(string="Title Brand")
    odoo_text_replacement = fields.Char(string='Powered By Text')
    #mail_powered_by = fields.Boolean('Mail Powered By', related='company_id.mail_powered_by')

    # @api.model
    # def fields_view_get(
    #         self, view_id=None, view_type="form", toolbar=False, submenu=False
    # ):
    #     ret_val = super().fields_view_get(
    #         view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
    #     )
    #
    #     page_name = ret_val["name"]
    #     if not page_name == "res.config.settings.view.form":
    #         return ret_val
    #
    #     doc = etree.XML(ret_val["arch"])
    #
    #     query = "//div[div[field[@widget='upgrade_boolean']]]"
    #     for item in doc.xpath(query):
    #         item.attrib["class"] = "d-none"
    #
    #     ret_val["arch"] = etree.tostring(doc)
    #     return ret_val

    @api.model
    def get_debranding_settings(self):
        IrDefault = self.env['ir.default'].sudo()
        whitelabel_favicon = IrDefault.get('res.config.settings', "whitelabel_favicon")

        title_brand = IrDefault.get('res.config.settings', "title_brand")
        if not title_brand:
            title_brand = self.website_name

        odoo_text_replacement = IrDefault.get('res.config.settings', "odoo_text_replacement")

        website_id = self.website_id and self.website_id.id or False
        if not website_id:
            website_id = self.env.context.get('website_id', False)

        if whitelabel_favicon:
            website_id = False

        attach_id = self.env['ir.attachment'].sudo().search([
                ('name', '=', 'Favicon'),
                ('website_id', '=', website_id)
            ])

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        favicon_url = base_url + '/web/image/?model=ir.attachment&id=' + str(attach_id.id) + '&field=datas'

        return {
            'title_brand': title_brand,
            'odoo_text_replacement': odoo_text_replacement,
            'favicon_url': favicon_url,
        }

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()

        whitelabel_favicon = False
        if self.whitelabel_favicon:
            whitelabel_favicon = self.whitelabel_favicon.decode("utf-8")
            IrDefault.set('res.config.settings', "whitelabel_favicon", whitelabel_favicon)
        else:
            IrDefault.set('res.config.settings', "whitelabel_favicon", False)

        IrDefault.set('res.config.settings', "title_brand", self.title_brand)
        IrDefault.set('res.config.settings', "odoo_text_replacement", self.odoo_text_replacement)

        website_id = self.website_id and self.website_id.id or False
        if whitelabel_favicon:
            website_id = False

        if not whitelabel_favicon and self.favicon:
            whitelabel_favicon = self.favicon

        attach_id = self.env['ir.attachment'].sudo().search([
            ('name', '=', 'Favicon'),
            ('website_id', '=', website_id)
        ])
        if attach_id:
            attach_id.write({
                'datas': whitelabel_favicon,
            })
        else:
            self.env['ir.attachment'].sudo().create({
                'name': 'Favicon',
                'datas': whitelabel_favicon,
                'public': True,
                'website_id': website_id
            })

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        whitelabel_favicon = IrDefault.get('res.config.settings', "whitelabel_favicon")
        title_brand = IrDefault.get('res.config.settings', "title_brand")
        odoo_text_replacement = IrDefault.get('res.config.settings', "odoo_text_replacement")
        res.update(
            whitelabel_favicon=whitelabel_favicon,
            title_brand=title_brand,
            odoo_text_replacement=odoo_text_replacement,
        )
        return res
