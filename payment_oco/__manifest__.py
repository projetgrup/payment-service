# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Order Checkout Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_system_sale'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/item.xml',
        'views/partner.xml',
        'views/sale.xml',
        'views/actions.xml',
        'views/menu.xml',
        'views/templates.xml',
        'views/settings.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_oco/static/src/scss/page.scss',
            'payment_oco/static/src/js/page.js',
        ],
    },
}
