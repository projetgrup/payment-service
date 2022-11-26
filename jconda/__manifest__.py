# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'jConda Connector',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1071,
    'depends': ['base'],
    'data': [
        'views/jconda.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
    ],
    'auto_install': True,
}
