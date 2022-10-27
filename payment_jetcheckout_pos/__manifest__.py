# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Jetcheckout Payment Acquirer - Point of Sale',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1455,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'point_of_sale',
        'payment_jetcheckout',
    ],
    'data': [
        'views/pos.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_jetcheckout_pos/static/src/js/pos.js',
        ],
    },
    'application': False,
}
