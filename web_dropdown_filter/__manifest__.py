# -*- coding: utf-8 -*-
{
    'name': 'Web: Dropdown Filter',
    'version': '1.0',
    'author': 'Bulutkobi',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'depends': ['web'],
    'data': ['views/templates.xml'],
    'auto_install': True,
    'assets': {
        'web.assets_backend': [
            'web_dropdown_filter/static/src/webclient/**/*',
            'web_dropdown_filter/static/src/scss/menu.scss',
        ],
        'web.assets_qweb': [
            'web_dropdown_filter/static/src/webclient/**/*',
        ],
        'web.assets_frontend': [
            'web_dropdown_filter/static/src/js/switch_website_menu.js',
            'web_dropdown_filter/static/src/xml/switch_website_menu.xml',
        ],
    }
}
