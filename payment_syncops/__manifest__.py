# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'syncOPS Payment Integration',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1455,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'payment_jetcheckout_system',
        'connector_syncops'
    ],
    'data': [
        'views/transaction.xml',
        'views/templates.xml',
        'report/company.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_qweb': [
            'payment_syncops/static/src/xml/connector.xml',
        ],
        'web.assets_frontend': [
            'payment_syncops/static/src/js/connector.js',
            'payment_syncops/static/src/scss/connector.scss',
        ],
    },
    'application': False,
    'auto_install': True,
    'images': ['static/description/icon.png'],
}
