# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Vendor Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_syncops', 'payment_system_subscription', 'payment_system_agreement'],
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
            'payment_vendor/static/src/scss/page.scss',
            'payment_vendor/static/src/js/page.js',
        ],
    },
}
