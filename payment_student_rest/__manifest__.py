# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Student Payment System - REST API',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'General',
    'depends': ['payment_student','base_rest','base_rest_datamodel','component'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
    ],
    'external_dependencies': {'python': ['jsondiff']},
}
