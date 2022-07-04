# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Jetcheckout Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1454,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'payment_jetcheckout',
        'sms_api'
    ],
    'data': [
        'data/data.xml',
        'views/company.xml',
        'views/transaction.xml',
        'views/templates.xml',
        'views/mail.xml',
        'views/user.xml',
        'views/item.xml',
        'views/partner.xml',
        'views/website.xml',
        'views/settings.xml',
        'views/dashboard.xml',
        'views/actions.xml',
        'report/company.xml',
        'wizards/send.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_qweb': [
            'payment_jetcheckout_system/static/src/xml/company.xml',
        ],
        'web.assets_backend': [
            'payment_jetcheckout_system/static/src/js/company.js',
            'payment_jetcheckout_system/static/src/scss/company.scss',
            'payment_jetcheckout_system/static/src/scss/send.scss',
        ],
        'web.assets_frontend': [
            'payment_jetcheckout_system/static/src/js/system.js',
        ],
    },
    'application': False,
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/icon.png'],
}
