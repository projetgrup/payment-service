# -*- coding: utf-8 -*-
# Copyright © 2023 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Jewelry Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_system_product', 'payment_syncops'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'views/item.xml',
        'views/partner.xml',
        'views/actions.xml',
        'views/menu.xml',
        'views/templates.xml',
        'views/settings.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_jewelry/static/src/scss/register.scss',
            'payment_jewelry/static/src/xml/register.xml',
            'payment_jewelry/static/src/js/register.js',
            'payment_jewelry/static/src/scss/page.scss',
            'payment_jewelry/static/src/xml/page.xml',
            'payment_jewelry/static/src/js/page.js',
        ],
    },
}
