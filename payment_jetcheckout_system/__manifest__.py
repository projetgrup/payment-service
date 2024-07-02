# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Paylox Payment System',
    'version': '1.16',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1454,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'sale',
        'sales_team',
        'payment_jetcheckout',
        'sms_api'
    ],
    'data': [
        'data/data.xml',
        'views/dashboard.xml',
        'views/company.xml',
        'views/acquirer.xml',
        'views/transaction.xml',
        'views/templates.xml',
        'views/mail.xml',
        'views/user.xml',
        'views/page.xml',
        'views/item.xml',
        'views/plan.xml',
        'views/partner.xml',
        'views/website.xml',
        'views/settings.xml',
        'views/actions.xml',
        'report/company.xml',
        'wizards/send.xml',
        'wizards/item.xml',
        'wizards/follower.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_qweb': [
            'payment_jetcheckout_system/static/src/xml/dashboard.xml',
            'payment_jetcheckout_system/static/src/xml/company.xml',
        ],
        'web.assets_backend': [
            'payment_jetcheckout_system/static/src/js/partner.js',
            'payment_jetcheckout_system/static/src/js/item.js',
            'payment_jetcheckout_system/static/src/js/menu.js',
            'payment_jetcheckout_system/static/src/js/dashboard.js',
            'payment_jetcheckout_system/static/src/js/company.js',
            'payment_jetcheckout_system/static/src/scss/backend.scss',
            'payment_jetcheckout_system/static/src/scss/company.scss',
            'payment_jetcheckout_system/static/src/scss/send.scss',
        ],
        'web.assets_frontend': [
            'payment_jetcheckout_system/static/src/xml/system.xml',
            'payment_jetcheckout_system/static/src/js/system.js',
            'payment_jetcheckout_system/static/src/js/flow.js',
            'payment_jetcheckout_system/static/src/scss/frontend.scss',
        ],
    },
    'application': False,
    'images': ['static/description/icon.png'],
}
