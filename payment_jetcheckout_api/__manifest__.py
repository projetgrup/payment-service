# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.
{
    'name': 'Jetcheckout Payment API',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Accounting/Payment Acquirers',
    'depends': [
        'payment_jetcheckout',
        'base_rest_datamodel',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/templates.xml',
        'views/views.xml'
    ],
    'assets': {
        #'web.assets_qweb': [
        #    'payment_jetcheckout_api/static/src/xml/templates.xml',
        #],
        'web.assets_frontend': [
            'payment_jetcheckout_api/static/src/js/page.js',
            'payment_jetcheckout_api/static/src/scss/font.scss',
            'payment_jetcheckout_api/static/src/scss/page.scss',
        ],
    },
    'images': ['static/description/icon.png'],
    'external_dependencies': {'python': ['jsondiff']},
}
