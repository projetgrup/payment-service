# -*- coding: utf-8 -*-
# Copyright © 2025 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'syncOPS Payment Integration',
    'version': '1.13',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1455,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'payment_jetcheckout_system',
        'connector_syncops'
    ],
    'data': [
        'data/data.xml',
        'views/partner.xml',
        'views/transaction.xml',
        'views/acquirer.xml',
        'views/templates.xml',
        'views/settings.xml',
        'views/user.xml',
        'views/item.xml',
        'wizards/sync.xml',
        'report/company.xml',
        'report/report.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'payment_syncops/static/src/js/button.js',
        ],
        'web.assets_frontend': [
            'payment_syncops/static/src/xml/connector.xml',
            'payment_syncops/static/src/js/connector.js',
            'payment_syncops/static/src/scss/connector.scss',
        ],
    },
    'application': False,
    'auto_install': True,
    'images': ['static/description/icon.png'],
}
