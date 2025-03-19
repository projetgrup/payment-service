# -*- coding: utf-8 -*-
{
    'name': 'OAuth2: Microsoft Azure',
    'version': '1.0',
    'category': 'Extra Tools',
    'author': 'Projet',
    'website': 'https://bulutkobi.io',
    'depends': ['auth_oauth'],
    'data': [
        'data/auth_oauth_provider_data.xml',
        'views/auth_oauth_provider_views.xml',
    ],
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': [
            'PyJWT',
        ]
    },
}
