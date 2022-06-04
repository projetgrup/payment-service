# -*- coding: utf-8 -*-
from odoo import models, fields
from datetime import date

class StudentSetting(models.Model):
    _name = 'res.student.setting'
    _description = 'Settings'

    is_discount_advance = fields.Boolean(string='Advance Payment Discount', default=False)
    discount_advance_ids = fields.One2many('res.student.discount', 'company_id', string='Advance Payment Discounts', copy=False)
    is_discount_sibling = fields.Boolean(string='Sibling Payment Discount', default=False)
    discount_sibling = fields.Float(string='Sibling Discount')
    discount_maximum = fields.Boolean(string='Select Maximum')
    privacy_policy = fields.Html(string='Privacy Policy', sanitize=False)
    sale_agreement = fields.Html(string='Distant Sale Agreement', sanitize=False)
    membership_agreement = fields.Html(string='Membership Agreement', sanitize=False)
    contact_page = fields.Html(string='Contact Page', sanitize=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    website_footer = fields.Html(string='Membership Agreement', sanitize=False)

class StudentPayment(models.Model):
    _name = 'res.student.payment'
    _description = 'Student Payment Items'
    _order = 'id desc'

    student_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    limited_student_id = fields.Many2one('res.partner', compute='_compute_student', store=False, readonly=False)
    parent_id = fields.Many2one('res.partner', related='student_id.parent_id', store=True, readonly=True, ondelete='restrict')
    school_id = fields.Many2one('res.student.school', related='student_id.school_id', store=True, readonly=True, ondelete='restrict')
    class_id = fields.Many2one('res.student.class', related='student_id.class_id', store=True, readonly=True, ondelete='restrict')
    bursary_id = fields.Many2one('res.student.bursary', related='student_id.bursary_id', store=True, readonly=True, ondelete='restrict')
    term_id = fields.Many2one('res.student.term', required=True, ondelete='restrict')
    payment_type_id = fields.Many2one('res.student.payment.type', required=True, ondelete='restrict')
    amount = fields.Monetary()
    paid = fields.Boolean(readonly=True)
    paid_amount = fields.Monetary(readonly=True)
    installment_count = fields.Integer(readonly=True)
    paid_date = fields.Datetime(readonly=True)
    transaction_ids = fields.Many2many('payment.transaction', 'transaction_payment_rel', 'payment_id', 'transaction_id', string='Student Payments')
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)
