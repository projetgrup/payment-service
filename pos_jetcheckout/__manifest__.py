# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Jetcheckout Payment Acquirer - Point of Sale Terminal',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1456,
    'category': 'Sales/Point of Sale',
    'depends': ['payment_jetcheckout_pos', 'sms_api'],
    'data': [
        'data/data.xml',
        'views/pos.xml',
        'views/templates.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'payment_jetcheckout/static/src/js/imask.js',
            'payment_jetcheckout/static/src/js/cards.js',
            'pos_jetcheckout/static/src/js/models.js',
            'pos_jetcheckout/static/src/js/pos_jetcheckout.js',
            'pos_jetcheckout/static/src/js/paymentScreen.js',
            'pos_jetcheckout/static/src/js/cardPopup.js',
            'pos_jetcheckout/static/src/js/linkPopup.js',
            'pos_jetcheckout/static/src/js/installmentPopup.js',
            'pos_jetcheckout/static/src/scss/payment.scss',
        ],
        'web.assets_qweb': [
            'pos_jetcheckout/static/src/xml/**/*',
        ],
    },
    'application': False,
}
