# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Payment System API',
    'version': '1.1',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_jetcheckout_system', 'payment_jetcheckout_api'],
    'data': [
        'security/ir.model.access.csv',
        'views/settings.xml',
    ],
}
