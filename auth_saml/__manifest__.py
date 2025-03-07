# -*- coding: utf-8 -*-
# Copyright © 2024 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.
{
    'name': 'SAML2 Authentication',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'license': 'LGPL-3',
    'sequence': 1453,
    'category': 'Tools',
    'depends': ['base_setup', 'web'],
    'external_dependencies': {
        'python': ['pysaml2'],
        'bin': ['xmlsec1'],
    },
    'data': [
        'data/ir_config_parameter.xml',
        'security/ir.model.access.csv',
        'views/auth_saml.xml',
        'views/res_config_settings.xml',
        'views/res_users.xml',
    ],
}
