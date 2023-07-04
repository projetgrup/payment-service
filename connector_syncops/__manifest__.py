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
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'auto_install': False,
}
