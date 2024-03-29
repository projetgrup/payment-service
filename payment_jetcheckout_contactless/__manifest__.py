# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Paylox Contactless Payment',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_jetcheckout'],
    'data': [
        'views/templates.xml',
        'views/acquirer.xml',
        'views/transaction.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_jetcheckout_contactless/static/src/js/page.js',
        ],
    },
    "external_dependencies": {
        "python": [
            "pycryptodome",
        ]
    },
}
