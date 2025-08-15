# -*- coding: utf-8 -*-
# Copyright © 2025 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Escrow Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_syncops', 'payment_system_agreement', 'payment_system_sale'],
    'data': [
        'security/security.xml',
        'data/data.xml',
        'views/ad.xml',
        'views/sale.xml',
        'views/item.xml',
        'views/partner.xml',
        'views/actions.xml',
        'views/menu.xml',
        'views/templates.xml',
        'views/settings.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_jetcheckout/static/src/lib/filepond/filepond.css',
            'payment_jetcheckout/static/src/lib/filepond/filepond.js',
            'payment_jetcheckout/static/src/lib/filepond/filepond_image_preview.css',
            'payment_jetcheckout/static/src/lib/filepond/filepond_image_preview.js',
            'payment_jetcheckout/static/src/lib/filepond/filepond_validate_type.js',
            'payment_jetcheckout/static/src/lib/filepond/filepond_validate_size.js',
            'payment_escrow/static/src/scss/page.scss',
            'payment_escrow/static/src/js/page.js',
        ],
    },
}
