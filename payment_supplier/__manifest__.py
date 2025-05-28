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
    'depends': ['payment_jetcheckout_system', 'payment_syncops'],
    'data': [
        'security/security.xml',
        'data/data.xml',
        'report/report.xml',
        'views/item.xml',
        'views/partner.xml',
        'views/actions.xml',
        'views/menu.xml',
        'views/settings.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'payment_supplier/static/src/scss/backend.scss',
        ],
        'web.assets_frontend': [
            'payment_supplier/static/src/scss/page.scss',
        ],
    },
}
