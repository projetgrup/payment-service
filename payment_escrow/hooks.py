# -- coding: utf-8 --
# Copyright © 2022 Projet (https://bulutkobi.io)
# Part of Paylox License. See LICENSE file for full copyright and licensing details.

from odoo import SUPERUSER_ID, api
from odoo.tools import config
import logging

_logger = logging.getLogger(__name__)



def post_init_hook(cr, registry):
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    products_to_update = env['product.product'].search([
        ('escrow_state', '=', False),
        ('system', '=', 'escrow')
    ])
    _logger.error(f"Found {len(products_to_update)} products with empty escrow_state")
    
    if products_to_update:
        products_to_update.write({'escrow_state': 'waiting'})
        print(f"Updated {len(products_to_update)} products with default escrow_state='waiting'")
    
    cr.execute("""
        UPDATE product_product 
        SET escrow_state = 'waiting' 
        WHERE escrow_state IS NULL
        AND system = 'escrow';
    """)
    
    affected_rows = cr.rowcount
    if affected_rows > 0:
        print(f"Updated {affected_rows} products with NULL escrow_state to 'waiting'")