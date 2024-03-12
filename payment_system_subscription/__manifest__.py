# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment System - Subscription',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1454,
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_system_sale', 'portal', 'rating'],
    'data': [
        'data/mail_template.xml',
        'data/sms_template.xml',
        'data/payment_subscription.xml',

        'report/payment_subscription_report.xml',
        'security/subscription_security.xml',
        'security/ir.model.access.csv',
        'security/sms_security.xml',

        'views/payment_subscription.xml',
        'views/account_analytic_account.xml',
        'views/payment_subscription_portal.xml',
        'views/sale_order.xml',
        'views/sms_composer.xml',
        'views/product_template.xml',
        'views/res_partner.xml',

        'wizard/payment_subscription_reason_wizard_views.xml',
        'wizard/payment_subscription_renew_wizard_views.xml',
        'wizard/payment_subscription_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/payment_system_subscription/static/src/scss/payment_subscription.scss',
        ],
        'web.assets_frontend': [
            '/payment_system_subscription/static/src/scss/portal_subscription.scss',
            '/payment_system_subscription/static/src/js/portal_subscription.js'
        ],
    },
    'images': ['static/description/icon.png'],
}
