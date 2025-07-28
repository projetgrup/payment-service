# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Mobile: Application',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'web_mobile_application/static/src/scss/main.scss',
            'web_mobile_application/static/src/js/main.js',
        ],
    },
}
