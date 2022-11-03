# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
# Set nginx settings to 'proxy_cookie_path / "/; secure; SameSite=none";'

{
    'name': 'Jetcheckout Payment Acquirer',
    'version': '1.4',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1453,
    'category': 'Accounting/Payment Acquirers',
    'depends': ['account_payment','website_payment'],
    'data': [
        'views/acquirer.xml',
        'views/transaction.xml',
        'views/partner.xml',
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
        'web.assets_frontend': [
            'payment_jetcheckout/static/src/js/imask.js',
            'payment_jetcheckout/static/src/js/cards.js',
            'payment_jetcheckout/static/src/js/framework.js',
            'payment_jetcheckout/static/src/js/payment_page.js',
            'payment_jetcheckout/static/src/js/payment_form.js',
            'payment_jetcheckout/static/src/scss/payment.scss',
        ],
    },
    'application': False,
    'uninstall_hook': 'uninstall_hook',
    'images': ['static/description/icon.png'],
}
