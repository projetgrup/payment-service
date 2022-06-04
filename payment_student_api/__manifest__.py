# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Student Payment System API',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'payment_student',
        'payment_jetcheckout_api'
    ],
    'data': [
        'views/views.xml',
    ],
    'external_dependencies': {'python': ['jsondiff']},
}
