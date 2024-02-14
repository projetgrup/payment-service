# -*- coding: utf-8 -*-
# Copyright © 2023 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment System - Sale',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1454,
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'sale',
        'payment_system_product',
    ],
    'data': [
        'views/sale.xml',
    ],
    'images': ['static/description/icon.png'],
}
