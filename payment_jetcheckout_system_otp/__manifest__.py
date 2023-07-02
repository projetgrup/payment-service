# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Paylox Payment System - OTP Login',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1455,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'payment_jetcheckout_system',
    ],
    'data': [
        'data/data.xml',
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
