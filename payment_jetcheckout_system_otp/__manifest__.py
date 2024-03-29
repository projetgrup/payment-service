# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Jetcheckout Payment System - OTP Login',
    'version': '1.1',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1455,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'payment_jetcheckout_system',
    ],
    'data': [
        'data/data.xml',
        'views/settings.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_jetcheckout_system_otp/static/src/js/frontend.js',
        ],
    },
    'application': False,
    'images': ['static/description/icon.png'],
}
