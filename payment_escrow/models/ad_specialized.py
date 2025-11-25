# -*- coding: utf-8 -*-
from odoo import models, fields, api


class EscrowAdVehicle(models.Model):
    _name = 'escrow.ad.vehicle'
    _description = 'Vehicle Advertisement Details'

    name = fields.Char(string='Name', default='Vehicle Details')
    ad_id = fields.Many2one('escrow.ad', string='Advertisement', required=True, ondelete='cascade', index=True)
    
    car_brand_id = fields.Many2one('escrow.car.brand', index=True)
    car_model_id = fields.Many2one('escrow.car.model', index=True)
    model_year = fields.Char(size=4, index=True)
    
    vin = fields.Char(string='Chassis (VIN)', size=17, index=True)
    plate = fields.Char(string='License Plate', index=True)
    license_serial_no = fields.Char(string='License Serial No')
    
    mileage = fields.Integer()
    engine_size = fields.Integer()
    engine_power = fields.Integer()
    
    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('lpg', 'LPG'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
        ('plug_in_hybrid', 'Plug-in Hybrid'),
    ], index=True)
    
    transmission = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('semi_automatic', 'Semi-Automatic'),
    ], index=True)
    
    body_type = fields.Selection([
        ('sedan', 'Sedan'),
        ('hatchback', 'Hatchback'),
        ('suv', 'SUV'),
        ('pickup', 'Pickup'),
        ('coupe', 'Coupe'),
        ('convertible', 'Convertible'),
        ('wagon', 'Wagon'),
        ('van', 'Van'),
        ('minivan', 'Minivan'),
    ], index=True)
    
    color = fields.Char()
    
    damage_status = fields.Selection([
        ('no_damage', 'No Damage'),
        ('painted', 'Painted'),
        ('changed', 'Changed Parts'),
        ('damaged', 'Damaged'),
    ], default='no_damage')
    
    damage_description = fields.Text()
    
    from_owner = fields.Boolean(string='From Owner', default=True)
    swap_available = fields.Boolean(string='Swap Available')



class EscrowAdRealEstate(models.Model):
    _name = 'escrow.ad.realestate'
    _description = 'Real Estate Advertisement Details'

    name = fields.Char(string='Name', default='Real Estate Details')
    ad_id = fields.Many2one('escrow.ad', string='Advertisement', required=True, ondelete='cascade', index=True)
    
    property_type = fields.Selection([
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('land', 'Land'),
        ('office', 'Office'),
        ('shop', 'Shop'),
        ('warehouse', 'Warehouse'),
        ('building', 'Building'),
    ], required=True, index=True)
    
    listing_type = fields.Selection([
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
    ], required=True, default='sale', index=True)
    
    net_area = fields.Float(string='Net Area (m²)')
    gross_area = fields.Float(string='Gross Area (m²)')
    
    room_count = fields.Selection([
        ('1+0', '1+0'),
        ('1+1', '1+1'),
        ('2+1', '2+1'),
        ('3+1', '3+1'),
        ('4+1', '4+1'),
        ('5+1', '5+1'),
        ('6+1', '6+1'),
        ('studio', 'Studio'),
    ])
    
    bathroom_count = fields.Integer()
    
    floor_number = fields.Integer()
    total_floors = fields.Integer()
    
    building_age = fields.Integer()
    
    heating_type = fields.Selection([
        ('none', 'None'),
        ('stove', 'Stove'),
        ('natural_gas', 'Natural Gas'),
        ('central', 'Central Heating'),
        ('floor_heating', 'Floor Heating'),
        ('air_conditioning', 'Air Conditioning'),
        ('solar', 'Solar'),
    ])
    
    dues_fee = fields.Float(string='Monthly Dues')
    
    furnished = fields.Boolean(string='Furnished')
    balcony = fields.Boolean(string='Balcony')
    elevator = fields.Boolean(string='Elevator')
    parking = fields.Boolean(string='Parking')
    garage = fields.Boolean(string='Garage')
    security = fields.Boolean(string='Security')
    has_pool = fields.Boolean(string='Pool')
    garden = fields.Boolean(string='Garden')
    
    title_deed_status = fields.Selection([
        ('ready', 'Ready'),
        ('condominium', 'Condominium'),
        ('shared', 'Shared'),
        ('land', 'Land'),
    ])
    
    deed_type = fields.Selection([
        ('standard', 'Standard'),
        ('agricultural', 'Agricultural'),
        ('zoned', 'Zoned'),
    ])
    
    zoning_status = fields.Char()
    island_number = fields.Char()
    parcel_number = fields.Char()
