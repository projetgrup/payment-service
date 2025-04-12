# -*- coding: utf-8 -*-
{
    'name': 'OAuth2: Microsoft Azure',
    'version': '1.0',
    'category': 'Extra Tools',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'depends': ['auth_multitenant'],
    'data': [
        'data/auth_oauth_provider.xml',
        'views/auth_oauth_provider.xml',
    ],
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': [
            'PyJWT',
        ]
    },
}
