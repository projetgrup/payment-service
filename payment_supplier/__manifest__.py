# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Supplier Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_jetcheckout_system',],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/item.xml',
        'views/token.xml',
        'views/partner.xml',
        'views/actions.xml',
        'views/menu.xml',
        'views/templates.xml',
        'views/settings.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'payment_supplier/static/src/scss/backend.scss',
            #'payment_supplier/static/src/js/backend.js',
        ],
        'web.assets_frontend': [
            'payment_supplier/static/src/scss/frontend.scss',
            'payment_supplier/static/src/js/frontend.js',
        ],
    },
}
