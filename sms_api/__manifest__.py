# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'SMS API',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'category': 'Hidden/Tools',
    'depends': ['sms'],
    'data': ['views/sms.xml'],
    'auto_install': True,
    'assets': {
        'web.assets_backend': [
            'sms_api/static/src/js/sms.js',
        ],
    },
}
