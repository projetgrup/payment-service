# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Student Payment System',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'General',
    'depends': ['payment_jetcheckout'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/mail.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'payment_student/static/src/xml/templates.xml',
        ],
        'web.assets_frontend': [
            'payment_student/static/src/js/student.js',
            'payment_student/static/src/scss/student.scss',
        ],
    },
}
