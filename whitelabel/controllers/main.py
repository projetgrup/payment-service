from odoo.addons.web.controllers import main


class Binary(main.Binary):

    def content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                      filename_field='name', unique=None, filename=None, mimetype=None,
                      download=None, width=0, height=0, crop=False, access_token=None,
                      **kwargs):
        if filename_field == 'favicon' and model == 'res.company':
            attach_id = self.env['ir.attachment'].sudo().search([
                ('name', '=', 'Favicon'),
                ('website_id', '=', False)
            ])
            if attach_id:
                return attach_id.datas

        return super(Binary, self).content_image(xmlid, model, id, field, filename_field, unique, filename, mimetype,
                                                 download, width, height, crop, access_token, **kwargs)
