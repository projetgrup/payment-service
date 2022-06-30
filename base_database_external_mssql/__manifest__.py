# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Microsoft SQL Database Integration',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'depends': ['base_database_external'],
    'data': [],
    "external_dependencies": {
        "python": [
            "pymssql",
        ]
    },
    'auto_install': True,
}
