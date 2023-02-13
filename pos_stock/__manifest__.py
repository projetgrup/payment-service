# -*- coding: utf-8 -*-
# Copyright © 2023 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Point of Sale Stock',
    'version': '1.0',
    'author': 'Projet',
    'license': 'LGPL-3',
    'sequence': 1459,
    'category': 'Sales/Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos.xml',
        'views/stock.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_stock/static/src/css/pos.scss',
            'pos_stock/static/src/js/db.js',
            'pos_stock/static/src/js/models.js',
            'pos_stock/static/src/js/StockPopup.js',
            'pos_stock/static/src/js/Components.js',
        ],
        'web.assets_qweb': [
            'pos_stock/static/src/xml/StockPopup.xml',
            'pos_stock/static/src/xml/ProductItem.xml',
            'pos_stock/static/src/xml/Orderline.xml',
        ]
    },
    'application': False,
}
