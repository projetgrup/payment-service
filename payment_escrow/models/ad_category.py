# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EscrowAdCategory(models.Model):
    _name = 'escrow.ad.category'
    _description = 'Advertisement Category'

    name = fields.Char(required=True, translate=True, index=True)
    complete_name = fields.Char(compute='_compute_complete_name', recursive=True, store=True, index=True)
    parent_id = fields.Many2one('escrow.ad.category', string='Parent Category', ondelete='cascade', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('escrow.ad.category', 'parent_id', string='Child Categories')
    
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    
    category_type = fields.Selection([
        ('vehicle', 'Vehicle'),
        ('realestate', 'Real Estate'),
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing & Accessories'),
        ('home', 'Home & Garden'),
        ('services', 'Services'),
        ('other', 'Other'),
    ], required=True, default='other', index=True)
    
    description = fields.Text(translate=True)
    image = fields.Binary(attachment=True)
    
    attribute_ids = fields.Many2many('escrow.ad.attribute', 'escrow_category_attribute_rel', 'category_id', 'attribute_id', string='Attributes')
    
    ad_count = fields.Integer(compute='_compute_ad_count')
    
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, index=True)

    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name
    
    def _compute_ad_count(self):
        for category in self:
            category.ad_count = self.env['escrow.ad'].search_count([('category_id', '=', category.id)])
    
    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))


class EscrowAdAttribute(models.Model):
    _name = 'escrow.ad.attribute'
    _description = 'Advertisement Attribute'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    
    attribute_type = fields.Selection([
        ('char', 'Text'),
        ('integer', 'Number'),
        ('float', 'Decimal'),
        ('boolean', 'Checkbox'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('selection', 'Selection'),
        ('many2one', 'Reference'),
        ('text', 'Long Text'),
        ('binary', 'Image/File'),
    ], required=True, default='char')
    
    relation_model = fields.Char(string='Related Model', help='Model name for many2one fields (e.g., escrow.car.brand)')
    
    required = fields.Boolean(default=False)
    help_text = fields.Text(translate=True)
    mask = fields.Char(string='Input Mask', help='Input mask for the field (e.g. 000-000-0000)')
    is_primary_image = fields.Boolean(string='Is Primary Image', default=False, 
                                       help='If true, this binary attribute will be saved to ad.image_1920 field')
    
    is_name_part = fields.Boolean(string='Use in Name', default=False, help='If checked, this attribute will be used to generate the ad name.')
    name_sequence = fields.Integer(string='Name Sequence', default=10, help='Sequence for name generation.')

    selection_option_ids = fields.One2many('escrow.ad.attribute.option', 'attribute_id', string='Selection Options')
    
    category_ids = fields.Many2many('escrow.ad.category', 'escrow_category_attribute_rel', 'attribute_id', 'category_id', string='Categories')
    
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, index=True)


class EscrowAdAttributeOption(models.Model):
    _name = 'escrow.ad.attribute.option'
    _description = 'Attribute Selection Option'
    _order = 'sequence, name'

    attribute_id = fields.Many2one('escrow.ad.attribute', required=True, ondelete='cascade', index=True)
    name = fields.Char(required=True, translate=True)
    value = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class EscrowAdAttributeValue(models.Model):
    _name = 'escrow.ad.attribute.value'
    _description = 'Advertisement Attribute Value'

    ad_id = fields.Many2one('escrow.ad', required=True, ondelete='cascade', index=True)
    attribute_id = fields.Many2one('escrow.ad.attribute', required=True, ondelete='restrict', index=True)
    attribute_type = fields.Selection(related='attribute_id.attribute_type', readonly=True)
    
    value_char = fields.Char()
    value_integer = fields.Integer()
    value_float = fields.Float()
    value_boolean = fields.Boolean()
    value_date = fields.Date()
    value_datetime = fields.Datetime()
    value_selection = fields.Char()
    value_many2one = fields.Integer(string='Many2one Value (ID)')
    value_reference = fields.Reference(selection='_selection_reference_models')
    value_text = fields.Text()
    value_binary = fields.Binary(attachment=True)
    value_binary_filename = fields.Char(string='Filename')
    
    display_value = fields.Char(compute='_compute_display_value', store=True)
    
    
    @api.model
    def _selection_reference_models(self):
        return [
            ('escrow.car.brand', 'Car Brand'),
            ('escrow.car.model', 'Car Model'),
            ('res.partner', 'Partner'),
        ]
    
    @api.depends('attribute_type', 'value_char', 'value_integer', 'value_float', 'value_boolean', 
                 'value_date', 'value_datetime', 'value_selection', 'value_many2one', 'value_reference', 'value_text', 'value_binary_filename')
    def _compute_display_value(self):
        for value in self:
            if value.attribute_type == 'char':
                value.display_value = value.value_char or ''
            elif value.attribute_type == 'integer':
                value.display_value = str(value.value_integer) if value.value_integer else ''
            elif value.attribute_type == 'float':
                value.display_value = str(value.value_float) if value.value_float else ''
            elif value.attribute_type == 'boolean':
                value.display_value = _('Yes') if value.value_boolean else _('No')
            elif value.attribute_type == 'date':
                value.display_value = value.value_date.strftime('%d.%m.%Y') if value.value_date else ''
            elif value.attribute_type == 'datetime':
                value.display_value = value.value_datetime.strftime('%d.%m.%Y %H:%M') if value.value_datetime else ''
            elif value.attribute_type == 'selection':
                value.display_value = value.value_selection or ''
            elif value.attribute_type == 'many2one' and value.value_many2one:
                # Many2one için ID'yi browse edip display_name al
                try:
                    if value.attribute_id.relation_model:
                        record = self.env[value.attribute_id.relation_model].sudo().browse(value.value_many2one)
                        value.display_value = record.display_name if record.exists() else ''
                    else:
                        value.display_value = str(value.value_many2one)
                except Exception:
                    value.display_value = str(value.value_many2one)
            elif value.attribute_type == 'text':
                value.display_value = value.value_text or ''
            elif value.attribute_type == 'binary':
                value.display_value = value.value_binary_filename or _('File attached')
            else:
                value.display_value = ''
