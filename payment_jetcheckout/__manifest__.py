# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Jetcheckout Payment Acquirer',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['account_payment','website_payment'],
    'data': [
        'views/acquirer.xml',
        'views/transaction.xml',
        'views/templates.xml',
        'wizards/signin.xml',
        'wizards/application.xml',
        'wizards/pos.xml',
        'wizards/campaign.xml',
        'report/report.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_qweb': [
            'payment_jetcheckout/static/src/xml/templates.xml',
        ],
        'web.assets_frontend': [
            'payment_jetcheckout/static/src/js/imask.js',
            'payment_jetcheckout/static/src/js/payment_page.js',
            'payment_jetcheckout/static/src/js/payment_form.js',
            'payment_jetcheckout/static/src/js/payment_card.js',
            'payment_jetcheckout/static/src/scss/payment.scss',
        ],
    },
    'application': True,
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/icon.png'],
}
