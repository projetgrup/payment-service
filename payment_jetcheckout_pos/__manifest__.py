# -*- coding: utf-8 -*-
# Copyright © 2022 Projet (https://www.jetcheckout.com)
# Part of JetCheckout License. See LICENSE file for full copyright and licensing details.

{
    'name': 'Jetcheckout Payment Acquirer - Point of Sale',
    'version': '1.0',
    'author': 'Projet',
    'website': 'https://www.jetcheckout.com',
    'license': 'LGPL-3',
    'sequence': 1455,
    'category': 'Sales/Point of Sale',
    'depends': ['point_of_sale', 'payment_jetcheckout'],
    'data': ['views/config.xml', 'views/transaction.xml'],
    'application': False,
    'auto_install': True,
}
