# -- coding: utf-8 --
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    "name": "White Label",
    'version': '1.0',
    "summary": "White Label",
    "license": "LGPL-3",
    "category": "Tools",
    "author": 'Projet',
    "website": 'https://www.jetcheckout.com',
    "excludes": ["web_enterprise"],
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
    ],
    "qweb": [
        'static/src/xml/base.xml',
        'static/src/xml/client_action.xml',
    ],
    "assets": {
        "web.assets_backend": [
            '/whitelabel/static/src/js/web_client.js',
            '/whitelabel/static/src/js/dialog.js',
            '/whitelabel/static/src/js/my_widget.js',
            '/whitelabel/static/src/js/user_menu.js'
        ],
        'web.assets_qweb': [
            'whitelabel/static/src/xml/dashboard.xml',
            'whitelabel/static/src/xml/base.xml',
            'whitelabel/static/src/xml/client_action.xml',
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
    "external_dependencies": {}
}
