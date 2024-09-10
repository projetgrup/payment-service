# -- coding: utf-8 --
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    "name": "White Label",
    'version': '1.0',
    "summary": "White Label",
    "license": "LGPL-3",
    'sequence': 1453,
    "category": "Tools",
    "author": 'Projet',
    "website": 'https://bulutkobi.io',
    "excludes": ["web_enterprise", "web_responsive"],
    "depends": [
        'base',
        'web',
        'website',
        'mail',
        'portal',
    ],
    "data": [
        'data/data.xml',
        'views/res_config_view.xml',
        'views/web_client_template.xml',
        'views/portal_templates.xml',
        'views/email_templates.xml',
        'views/disable_odoo.xml',
        'views/ir_ui_menu.xml',
        'views/res_users.xml',
        'views/web.xml'
    ],
    "qweb": [
        'static/src/xml/base.xml',
        'static/src/xml/client_action.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            "/whitelabel/static/src/legacy/js/website_apps_menu.js",
            "/whitelabel/static/src/legacy/scss/website_apps_menu.scss",
        ],
        "web.assets_backend": [
            "/whitelabel/static/src/legacy/scss/web_responsive.scss",
            "/whitelabel/static/src/legacy/js/web_responsive.js",
            "/whitelabel/static/src/legacy/scss/kanban_view_mobile.scss",
            "/whitelabel/static/src/legacy/js/kanban_renderer_mobile.js",
            "/whitelabel/static/src/components/ui_context.esm.js",
            "/whitelabel/static/src/components/apps_menu/apps_menu.scss",
            "/whitelabel/static/src/components/apps_menu/apps_menu.esm.js",
            "/whitelabel/static/src/components/navbar/main_navbar.scss",
            "/whitelabel/static/src/components/control_panel/control_panel.scss",
            "/whitelabel/static/src/components/control_panel/control_panel.esm.js",
            "/whitelabel/static/src/components/search_panel/search_panel.scss",
            "/whitelabel/static/src/components/search_panel/search_panel.esm.js",
            "/whitelabel/static/src/components/attachment_viewer/attachment_viewer.scss",
            "/whitelabel/static/src/components/attachment_viewer/attachment_viewer.esm.js",
            "/whitelabel/static/src/components/hotkey/hotkey.scss",

            "/whitelabel/static/src/js/dialog.js",
            "/whitelabel/static/src/js/my_widget.js",
            "/whitelabel/static/src/js/user_menu.js",
        ],
        'web.assets_qweb': [
            "/whitelabel/static/src/legacy/xml/form_buttons.xml",
            "/whitelabel/static/src/components/apps_menu/apps_menu.xml",
            "/whitelabel/static/src/components/control_panel/control_panel.xml",
            "/whitelabel/static/src/components/navbar/main_navbar.xml",
            "/whitelabel/static/src/components/search_panel/search_panel.xml",
            "/whitelabel/static/src/components/attachment_viewer/attachment_viewer.xml",
            "/whitelabel/static/src/components/hotkey/hotkey.xml",

            "/whitelabel/static/src/xml/dashboard.xml",
            "/whitelabel/static/src/xml/base.xml",
            "/whitelabel/static/src/xml/client_action.xml",
        ],
        'web._assets_primary_variables': [
            "/whitelabel/static/src/scss/primary_variables_custom.scss",
        ],
        'web._assets_secondary_variablesweb.assets_backend': [
            "/whitelabel/static/src/scss/fields_extra_custom.scss",
        ],
        'web._assets_secondary_variables': [
            "/whitelabel/static/src/scss/secondary_variables.scss",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": False,
    "external_dependencies": {},
    "post_init_hook": 'post_init_hook'
}
