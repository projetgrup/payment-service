# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Point of Sale Sync',
    'version': '1.0',
    'author': 'Projet',
    'license': 'LGPL-3',
    'sequence': 1458,
    'category': 'Sales/Point of Sale',
    'depends': ['bus', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_sync/static/src/js/*',
            'pos_sync/static/src/scss/*',
        ],
        'web.assets_qweb': [
            'pos_sync/static/src/xml/**/*',
        ],
    },
    'application': False,
}
