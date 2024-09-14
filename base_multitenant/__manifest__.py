# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Multi-Tenant Architecture',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1000,
    'depends': ['base'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'base_multitenant/static/src/js/company_menu.js',
            'base_multitenant/static/src/scss/company_menu.scss',
        ],
        'web.assets_qweb': [
            'base_multitenant/static/src/xml/company_menu.xml',
        ],
    },
}
