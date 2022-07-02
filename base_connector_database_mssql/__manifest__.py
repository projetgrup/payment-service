# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Connector - Microsoft SQL Database',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Hidden',
    'depends': ['base_connector_database'],
    'data': ['data/data.xml'],
    "external_dependencies": {
        "python": [
            "pymssql",
        ]
    },
    'auto_install': True,
}
