# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

{
    'name': 'OAuth: Multi-Tenant Architecture',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1000,
    'depends': ['base_multitenant', 'auth_oauth'],
    'data': [
        'views/auth_oauth_provider.xml',
    ],
}
