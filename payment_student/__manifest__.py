# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Student Payment System',
    'version': '1.1',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': ['payment_jetcheckout_system'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/item.xml',
        'views/student.xml',
        'views/partner.xml',
        'views/actions.xml',
        'views/menu.xml',
        'views/templates.xml',
        'views/settings.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'payment_student/static/src/xml/templates.xml',
        ],
        'web.assets_backend': [
            'payment_student/static/src/scss/backend.scss',
        ],
        'web.assets_frontend': [
            'payment_student/static/src/js/frontend.js',
            'payment_student/static/src/scss/frontend.scss',
        ],
    },
}
