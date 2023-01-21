# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale Advanced',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1457,
    'category': 'Sales/Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'data/data.xml',
        'views/pos.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_advanced/static/src/js/models.js',
            'pos_advanced/static/src/js/addressScreen.js',
            'pos_advanced/static/src/js/paymentScreen.js',
            'pos_advanced/static/src/js/ActionpadWidget.js',
            'pos_advanced/static/src/js/ProductScreen.js',
            'pos_advanced/static/src/js/ClientDetailsEdit.js',
            'pos_advanced/static/src/js/bankPopup.js',
            'pos_advanced/static/src/js/addressPopup.js',
            'pos_advanced/static/src/scss/pos.scss',
        ],
        'web.assets_qweb': [
            'pos_advanced/static/src/xml/**/*',
        ],
    },
    'application': False,
}
