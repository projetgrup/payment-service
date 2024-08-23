from odoo import models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def create(self, vals):
        res = super(ResCompany, self).create(vals)
        auto_create_website = self.env['ir.config_parameter'].sudo().get_param('theme_paylox.auto_create_website', 'False')
        if auto_create_website == 'True':
            res._create_default_website_payment_theme()
        return res

    def _create_default_website_payment_theme(self):
        theme = self.env.ref('base.module_theme_paylox')
        website = self.env['website'].sudo().create({
            'name': self.name,
            'logo': self.logo,
            'company_id': self.id,
            'theme_id': theme.id,
        })

        standard_homepage = self.env.ref('website.homepage', raise_if_not_found=False)
        if not standard_homepage:
            return

        new_homepage_view = '''<t name="Homepage" t-name="website.homepage%s">
    <t t-call="website.layout">
        <t t-set="no_footer" t-value="True"/>
        <t t-set="pageName" t-value="'homepage'"/>
        <div id="wrap" class="oe_structure oe_empty">
            <section class="s_parallax parallax s_parallax_is_fixed bg-black-50 o_half_screen_height o_colored_level" data-scroll-background-ratio="1" data-snippet="s_parallax" data-name="Parallax" style="background-image: none;">
                <span class="s_parallax_bg oe_img_bg o_bg_img_center" style="background-image: url(/theme_paylox/static/description/s_cover.svg); background-position: 50%% 75%%;"/>
                <div class="o_we_bg_filter bg-black-50"/>
                <div class="oe_structure oe_empty" data-original-title="" title="" aria-describedby="">
                    <section class="s_cover parallax pb0 pt192 o_cc o_cc5 o_colored_level" data-scroll-background-ratio="0" data-oe-shape-data="{&quot;shape&quot;:&quot;web_editor/Blocks/04&quot;,&quot;flip&quot;:[&quot;x&quot;]}" data-snippet="s_cover" data-name="Cover" style="background-image: none;">
                        <span class="s_parallax_bg oe_img_bg" style="background-position: 50%% 0;background-image:url('/theme_paylox/static/description/s_cover.svg?c1=rgba%%28255%%2C+255%%2C+255%%2C+0.17%%29')"/>
                        <div class="o_we_shape o_web_editor_Blocks_04 o_we_flip_x"/>
                        <div class="container s_allow_columns">
                        <div class="row">
                            <div class="o_colored_level col-lg-10">
                                <h1><t t-out="res_company.name">Company name</t> | Online Tahsilat Sistemi</h1>
                                <p>&amp;nbsp;</p>
                                <p>
                                    <a href="/web/login" class="mb-2 btn btn-primary btn-lg" data-original-title="" title="">GİRİŞ YAP</a>&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;
                                    <a class="mb-2 btn btn-secondary btn-lg" href="/otp" data-original-title="" title="">ANINDA ŞİFRE İLE GİRİŞ YAP</a>
                                </p>
                            </div>
                            <div class="o_colored_level col-lg-6">
                                <img src="/theme_paylox/static/description/s_cover_person.svg?c1=o-color-1" style="width: 100%%;" alt="" loading="lazy"/>
                            </div>
                        </div>
                        </div>
                    </section>
                </div>
            </section>
        </div>
    </t>
</t>''' % (website.id)
        standard_homepage.with_context(website_id=website.id).arch_db = new_homepage_view
