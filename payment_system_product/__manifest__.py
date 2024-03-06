# -*- coding: utf-8 -*-
# Copyright © 2023 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment System - Product',
    'version': '1.1',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1454,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'product',
        'payment_jetcheckout_system',
    ],
    'data': [
        #'views/settings.xml',
        'views/product.xml',
        'views/templates.xml',
        'security/security.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'payment_system_product/static/src/xml/product.xml',
            'payment_system_product/static/src/xml/page.xml',
        ],
        'web.assets_frontend': [
            'payment_system_product/static/src/scss/flow.scss',
            'payment_system_product/static/src/scss/page.scss',
            'payment_system_product/static/src/js/flow.js',
            'payment_system_product/static/src/js/page.js',
        ],
        'web.assets_backend': [
            'payment_system_product/static/src/js/product.js',
        ],
    },
    'images': ['static/description/icon.png'],
}
