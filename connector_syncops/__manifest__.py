# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'syncOPS Connector',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1071,
    'depends': ['base'],
    'data': [
        'views/config.xml',
        'views/syncops.xml',
        'wizards/log.xml',
        'wizards/sync.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'connector_syncops/static/src/xml/button.xml',
            'connector_syncops/static/src/xml/view.xml',
        ],
        'web.assets_backend': [
            'connector_syncops/static/src/js/button.js',
            'connector_syncops/static/src/js/view.js',
        ],
    },
    'auto_install': False,
}
