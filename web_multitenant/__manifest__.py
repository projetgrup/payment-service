# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Web: Multi-Tenant Architecture',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1000,
    'depends': ['base_multitenant', 'website'],
    'data': [
        'views/templates.xml',
        'views/website.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'web_multitenant/static/src/js/website_menu.js',
            'web_multitenant/static/src/xml/website_menu.xml',
        ],
    },
}
