# -*- coding: utf-8 -*-
# Copyright © 2023 Projet (https://bulutkobi.io)
# Part of Projet License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Security: Audit',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1455,
    'category': 'Hidden',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'views/audit.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sec_audit/static/src/js/audit.js',
        ],
    },
}
