# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    Category = env['escrow.ad.category']
    vehicle_cat = Category.search([('category_type', '=', 'vehicle')], limit=1)
    if not vehicle_cat:
        vehicle_cat = Category.create({
            'name': 'Vehicle',
            'category_type': 'vehicle',
        })
    else:
        _logger.error(f"Found 'Vehicle' category with ID: {vehicle_cat.id}")

    Attribute = env['escrow.ad.attribute']
    
    def get_or_create_attr(name, technical_name, attr_type, relation_model=False, is_name_part=False, sequence=10):
        attr = Attribute.search([('technical_name', '=', technical_name)], limit=1)
        if not attr:
            attr = Attribute.create({
                'name': name,
                'technical_name': technical_name,
                'attribute_type': attr_type,
                'relation_model': relation_model,
                'is_name_part': is_name_part,
                'name_sequence': sequence,
                'category_ids': [(4, vehicle_cat.id)],
                'is_primary_image': technical_name == 'photo',
            })
        else:
            if vehicle_cat.id not in attr.category_ids.ids:
                attr.write({'category_ids': [(4, vehicle_cat.id)]})
        return attr

    attr_plate = get_or_create_attr('Plate', 'plate', 'char', is_name_part=True, sequence=1)
    attr_brand = get_or_create_attr('Brand', 'brand_id', 'many2one', relation_model='escrow.car.brand', is_name_part=True, sequence=2)
    attr_model = get_or_create_attr('Model', 'model_id', 'many2one', relation_model='escrow.car.model', is_name_part=True, sequence=3)
    attr_year = get_or_create_attr('Year', 'year', 'integer', is_name_part=True, sequence=4)
    attr_vin = get_or_create_attr('VIN', 'vin', 'char')
    attr_license_serial = get_or_create_attr('License Serial No', 'license_serial_no', 'char')
    attr_photos = get_or_create_attr('Photos', 'photo', 'binary')

    Product = env['product.product']
    Ad = env['escrow.ad']
    AdValue = env['escrow.ad.attribute.value']

    cr.execute("""
        SELECT pp.id 
        FROM product_product pp
        JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE pt.system = 'escrow'
    """)
    product_ids = [row[0] for row in cr.fetchall()]
    products = Product.sudo().browse(product_ids)

    for product in products:
        existing_ad = Ad.search([('payment_item_id', '=', product.escrow_payment_item_id.id)], limit=1)
        if existing_ad:
            continue

        state_map = {
            'waiting': 'waiting',
            'new': 'new',
            'sold': 'sold',
            'cancel': 'cancelled',
        }
        ad_state = state_map.get(product.escrow_state, 'draft')

        sale_state = False
        if ad_state == 'new':
            if product.escrow_payment_item_id and product.escrow_payment_item_id.paid:
                 sale_state = 'waiting_official_doc'
            else:
                 sale_state = 'waiting_payment'
        elif ad_state == 'sold':
            sale_state = 'transferred'

        owner_id = product.escrow_owner_id.id
        broker_id = product.broker_id.id

        ad_vals = {
            'name': product.name,
            'category_id': vehicle_cat.id,
            'owner_id': owner_id,
            'broker_id': broker_id,
            'customer_ids': [(6, 0, product.escrow_customer_ids.ids)],
            'state': ad_state,
            'sale_state': sale_state,
            'price': product.list_price,
            'currency_id': product.currency_id.id,
            'payment_item_id': product.escrow_payment_item_id.id,
            'official_sale_document': product.escrow_ad_official_sale_img,
            'company_id': product.company_id.id or env.company.id,
            'image_1920': product.image_1920,
            'description': product.description_sale,
        }
        
        ad = Ad.create(ad_vals)

        if product.escrow_ad_sale_img:
             env['escrow.ad.image'].create({
                 'ad_id': ad.id,
                 'image': product.escrow_ad_sale_img,
                 'is_main': False,
             })

        if product.escrow_payment_item_id:
            product.escrow_payment_item_id.write({'ad_id': ad.id})

        if product.escrow_car_plate:
            AdValue.create({
                'ad_id': ad.id,
                'attribute_id': attr_plate.id,
                'value_char': product.escrow_car_plate,
            })

        if product.escrow_car_brand_id:
            AdValue.create({
                'ad_id': ad.id,
                'attribute_id': attr_brand.id,
                'value_many2one': product.escrow_car_brand_id.id,
            })

        if product.escrow_car_model_id:
            AdValue.create({
                'ad_id': ad.id,
                'attribute_id': attr_model.id,
                'value_many2one': product.escrow_car_model_id.id,
            })

        if product.escrow_car_model_year:
            year_val = int(product.escrow_car_model_year)
            AdValue.create({
                'ad_id': ad.id,
                'attribute_id': attr_year.id,
                'value_integer': year_val,
            })

        if product.escrow_car_vin:
            AdValue.create({
                'ad_id': ad.id,
                'attribute_id': attr_vin.id,
                'value_char': product.escrow_car_vin,
            })

        if product.escrow_license_serial_no:
            AdValue.create({
                'ad_id': ad.id,
                'attribute_id': attr_license_serial.id,
                'value_char': product.escrow_license_serial_no,
            })
        
        if product.image_1920:
            AdValue.create({
                'ad_id': ad.id,
                'attribute_id': attr_photos.id,
                'value_binary': product.image_1920,

            })

        cr.execute("""
            UPDATE mail_message 
            SET model = 'escrow.ad', res_id = %s 
            WHERE model = 'product.product' AND res_id = %s
        """, (ad.id, product.id))
        
        cr.execute("""
            UPDATE mail_activity 
            SET res_model = 'escrow.ad', res_id = %s 
            WHERE res_model = 'product.product' AND res_id = %s
        """, (ad.id, product.id))
        
        # cr.execute("""
        #     UPDATE mail_followers 
        #     SET res_model = 'escrow.ad', res_id = %s 
        #     WHERE res_model = 'product.product' AND res_id = %s
        # """, (ad.id, product.id))
        
        cr.execute("""
            UPDATE ir_attachment 
            SET res_model = 'escrow.ad', res_id = %s 
            WHERE res_model = 'product.product' AND res_id = %s
        """, (ad.id, product.id))
            
        ad._compute_name()

    _logger.error("Migration 1.4 completed.")
