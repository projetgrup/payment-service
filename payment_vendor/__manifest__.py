# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Vendor Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_syncops'],
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
            'payment_vendor/static/src/scss/frontend.scss',
            'payment_vendor/static/src/js/frontend.js',
        ],
    },
}
