# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _compute_student_payment_count(self):
        for tx in self:
            tx.student_payment_count = len(tx.student_payment_ids)

    student_payment_ids = fields.Many2many('res.student.payment', 'transaction_payment_rel', 'transaction_id', 'payment_id', string='Student Payments')
    student_payment_count = fields.Integer(compute='_compute_student_payment_count')

    def action_student_payments(self):
        self.ensure_one()
        action = self.env.ref('payment_student.action_payment').sudo().read()[0]
        action['domain'] = [('id', 'in', self.student_payment_ids.ids)]
        action['context'] = {'create': False, 'edit': False, 'delete': False}
        return action

    def _jetcheckout_process_query(self, vals):
        super()._jetcheckout_process_query(vals)
        if vals.get('successful') and not vals.get('cancelled'):
            self.mapped('student_payment_ids').write({'paid': True, 'paid_date': datetime.now(), 'installment_count': self.jetcheckout_installment_count})

    def jetcheckout_cancel(self):
        super().jetcheckout_cancel()
        self.mapped('student_payment_ids').write({'paid': False, 'paid_date': False, 'paid_amount': 0, 'installment_count': 0})

class StudentPaymentTable(models.TransientModel):
    _name = 'res.student.payment.table'
    _description = 'Payment Table'

    table = fields.Html(string='Payment Table', sanitize=False, readonly=True)

class StudentSetting(models.Model):
    _name = 'res.student.setting'
    _description = 'Settings'

    is_discount_advance = fields.Boolean(string='Advance Payment Discount', default=False)
    discount_advance_ids = fields.One2many('res.student.discount', 'setting_id', string='Advance Payment Discounts', copy=False)
    is_discount_sibling = fields.Boolean(string='Sibling Payment Discount', default=False)
    discount_sibling = fields.Float(string='Sibling Discount')
    discount_maximum = fields.Boolean(string='Select Maximum')
    privacy_policy = fields.Html(string='Privacy Policy', sanitize=False)
    sale_agreement = fields.Html(string='Distant Sale Agreement', sanitize=False)
    membership_agreement = fields.Html(string='Membership Agreement', sanitize=False)
    contact_page = fields.Html(string='Contact Page', sanitize=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    website_footer = fields.Html(string='Membership Agreement', sanitize=False)

    @api.model
    def get_settings(self, company=None):
        if not company:
            company = self.env.company
        return self.sudo().search([('company_id','=',company.id)], limit=1)

    def _get_setting_line(self):
        today = date.today()
        return self.env['res.student.discount'].sudo().search([
            ('setting_id','=',self.id),
            '|',('date_start','=',False),('date_start','<=',today),
             '|',('date_end','=',False),('date_end','>=',today),
        ], limit=1, order='id desc')

    def get_setting_discount(self):
        self.ensure_one()
        line = self._get_setting_line()
        return line.percentage if line else 0

    @api.model
    def action_settings(self):
        vals = {
            'type': 'ir.actions.act_window',
            'res_model': 'res.student.setting',
            'name': _('Settings'),
            'view_mode': 'form',
            'target': 'new',
            'context': {'create': False},
        }
        setting = self.get_settings()
        if setting:
            vals['res_id'] = setting.id
        return vals

class StudentDiscount(models.Model):
    _name = 'res.student.discount'
    _description = 'Payment Discounts'
    _order = 'id desc'

    setting_id = fields.Many2one('res.student.setting', string='Discount Start Date', ondelete='cascade')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    installment = fields.Integer(string='Installment')
    percentage = fields.Integer(string='Discount (%)')
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)

    @api.model
    def create(self, vals):
        if 'date_start' in vals and 'date_end' in vals and vals['date_start'] > vals['date_end']:
            raise UserError(_('Start date cannot be higher than end date'))
        if 'percentage' in vals and vals['percentage'] <= 0:
            raise UserError(_('Discount percentage must be higher than zero'))
        if 'installment' in vals and vals['installment'] <= 0:
            raise UserError(_('Installment must be higher than zero'))
        return super().create(vals)

    def write(self, vals):
        if 'date_start' in vals and 'date_end' in vals and vals['date_start'] > vals['date_end']:
            raise UserError(_('Start date cannot be higher than end date'))
        if 'percentage' in vals and vals['percentage'] <= 0:
            raise UserError(_('Discount percentage must be higher than zero'))
        if 'installment' in vals and vals['installment'] <= 0:
            raise UserError(_('Installment must be higher than zero'))
        return super().write(vals)

    @api.model
    def create(self, vals):
        if 'date_start' in vals and 'date_end' in vals and vals['date_start'] > vals['date_end']:
            raise UserError(_('Start date cannot be higher than end date'))
        if 'percentage' in vals and vals['percentage'] <= 0:
            raise UserError(_('Discount percentage must be higher than zero'))
        return super().create(vals)

class StudentSchool(models.Model):
    _name = 'res.student.school'
    _description = 'Schools'
    _order = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    code = fields.Char()
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)

class StudentClass(models.Model):
    _name = 'res.student.class'
    _description = 'Classes'
    _order = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    code = fields.Char()
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)

class StudentTerm(models.Model):
    _name = 'res.student.term'
    _description = 'Terms'
    _order = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    code = fields.Char()
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)

class StudentBursary(models.Model):
    _name = 'res.student.bursary'
    _description = 'Bursaries'
    _order = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    percentage = fields.Integer(string='Discount (%)')
    code = fields.Char()
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)

    def name_get(self):
        res = []
        for bursary in self:
            name = '%s - %%%s' % (bursary.name, bursary.percentage)
            res.append((bursary.id, name))
        return res

class StudentPaymentType(models.Model):
    _name = 'res.student.payment.type'
    _description = 'Payment Types'
    _order = 'name'

    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    code = fields.Char()
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)

class StudentPaymentTemplate(models.Model):
    _name = 'res.student.payment.template'
    _description = 'Student Payment Template'
    _order = 'id desc'

    school_id = fields.Many2one('res.student.school', required=True, ondelete='restrict')
    class_id = fields.Many2one('res.student.class', ondelete='restrict')
    term_id = fields.Many2one('res.student.term', required=True, ondelete='restrict')
    payment_type_id = fields.Many2one('res.student.payment.type', required=True, ondelete='restrict')
    amount = fields.Monetary(required=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one(related='company_id.currency_id', store=True, readonly=True)

class StudentPayment(models.Model):
    _name = 'res.student.payment'
    _description = 'Student Payment Items'
    _order = 'id desc'

    def _compute_name(self):
        for payment in self:
            payment.name = '%s (%s)' % (payment.student_id.name, payment.term_id.name)

    @api.depends('student_id')
    def _compute_student(self):
        for payment in self:
            if payment.limited_student_id.id != payment.student_id.id:
                payment.limited_student_id = payment.student_id.id

    @api.depends('limited_student_id')
    def _set_student(self):
        for payment in self:
            if payment.student_id.id != payment.limited_student_id.id:
                payment.student_id = payment.limited_student_id.id

    name = fields.Char(compute='_compute_name')
    student_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    limited_student_id = fields.Many2one('res.partner', compute='_compute_student', inverse='_set_student')
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

    @api.onchange('student_id','term_id','payment_type_id')
    def onchange_student_id(self):
        if self.school_id and self.class_id and self.term_id and self.payment_type_id:
            template = self.env['res.student.payment.template'].search([
                ('school_id','=',self.school_id.id),
                '|', ('class_id','=',self.class_id.id), ('class_id','=',False),
                ('term_id','=',self.term_id.id),
                ('payment_type_id','=',self.payment_type_id.id),
                ('company_id','=',self.company_id.id),
            ], limit=1)
            if template:
                self.amount = template.amount

    def is_sibling_paid(self):
        self.ensure_one()
        return self.search_count([
            ('student_id','!=',self.student_id.id),
            ('parent_id','=',self.parent_id.id),
            ('term_id','=',self.term_id.id),
            ('payment_type_id','=',self.payment_type_id.id),
            ('paid','=',True)
        ]) and True or False

    def action_transaction(self):
        self.ensure_one()
        action = self.env.ref('payment.action_payment_transaction').sudo().read()[0]
        action['domain'] = [('id', 'in', self.transaction_ids.ids)]
        action['context'] = {'create': False, 'edit': False, 'delete': False}
        return action

    def action_payment_table(self):
        self = self.filtered(lambda x: not x.paid)
        if not self:
            raise UserError(_('Payment table can be calculated only for non paid payment items'))
        payment_table = self.env['res.student.payment.table'].sudo().create({
            'table': self.env['ir.ui.view'].sudo()._render_template('payment_student.student_payment_table', {'vals': self.get_payment_table()})
        })
        action = self.env.ref('payment_student.action_payment_table').sudo().read()[0]
        action['res_id'] = payment_table.id
        return action

    def get_payment_table(self):
        if len(self.mapped('company_id')) != 1:
            raise UserError(_('Payment table cannot be related to more than one company'))

        company = self.mapped('company_id')
        settings = self.env['res.student.setting'].sudo().get_settings(company=company)
        if not settings:
            raise UserError(_('Please create a company payment settings to contine'))

        currency = company.currency_id
        precision = currency.decimal_places or 2
        student_ids = []
        payment_ids = []
        bursary_ids = []
        students = []
        payments = []
        bursaries = []
        siblings = []
        discounts = []
        subpayments = []
        subsiblings = []
        subbursaries = []
        totals = []

        for line in self:
            student_id = line.student_id
            bursary_id = line.bursary_id
            term_id = line.term_id
            type_id = line.payment_type_id

            if (term_id.id,type_id.id) not in payment_ids:
                payment_ids.append([term_id.id, type_id.id])
                payments.append({
                    'term_id': term_id.id,
                    'type_id': type_id.id,
                    'name': ' | '.join([term_id.name, type_id.name]),
                    'amount': [],
                })

            if bursary_id not in bursary_ids:
                bursary_ids.append(bursary_id.id)
                bursaries.append({
                    'id': bursary_id.id,
                    'name': bursary_id.name,
                    'amount': [],
                })

            if student_id not in student_ids:
                student_ids.append(student_id.id)
                students.append({
                    'id': student_id.id,
                    'name': student_id.name,
                })

        student_ids.sort()
        payment_ids.sort(key=lambda x: x[0])
        bursary_ids.sort()
        students.sort(key=lambda x: x['id'])
        payments.sort(key=lambda x: (x['term_id'], x['type_id']))
        bursaries.sort(key=lambda x: x['id'])

        for student in student_ids:
            for payment in payments:
                payment['amount'].append({'id': student, 'amount': 0})
            for bursary in bursaries:
                bursary['amount'].append({'id': student, 'amount': 0})
            siblings.append({'id': student, 'amount': 0})
            discounts.append({'id': student, 'amount': 0})
            subpayments.append({'id': student, 'amount': 0})
            subsiblings.append({'id': student, 'amount': 0})
            subbursaries.append({'id': student, 'amount': 0})
            totals.append({'id': student, 'amount': 0})

        advance_discount = settings.get_setting_discount()
        sibling_discount = 0
        if len(siblings) > 1 or len(siblings) == 1 and any(line.is_sibling_paid() for line in self):
            sibling_discount = settings.discount_sibling if settings.is_discount_sibling else 0

        for line in self:
            student_id = line.student_id.id
            bursary_id = line.bursary_id.id
            term_id = line.term_id.id
            type_id = line.payment_type_id.id
            amount = line.amount
            discount_amount = advance_discount / -100
            sibling_amount = sibling_discount / -100
            bursary_amount = line.bursary_id.percentage / -100

            if settings.discount_maximum:
                if sibling_amount > bursary_amount:
                    sibling_amount = 0
                else:
                    bursary_amount = 0

            payment = list(filter(lambda x: x['term_id'] == term_id and x['type_id'] == type_id, payments))[0]
            payment_item = list(filter(lambda x: x['id'] == student_id, payment['amount']))[0]
            payment_item['amount'] += round(amount, precision)

            subpayment_item = list(filter(lambda x: x['id'] == student_id, subpayments))[0]
            subpayment_item['amount'] += round(amount, precision)

            sibling_item = list(filter(lambda x: x['id'] == student_id, siblings))[0]
            sibling_item['amount'] += round(subpayment_item['amount'] * sibling_amount, precision)

            subsibling_item = list(filter(lambda x: x['id'] == student_id, subsiblings))[0]
            subsibling_item['amount'] += round(sibling_item['amount'] + subpayment_item['amount'], precision)

            bursary = list(filter(lambda x: x['id'] == bursary_id, bursaries))[0]
            bursary_item = list(filter(lambda x: x['id'] == student_id, bursary['amount']))[0]
            bursary_item['amount'] += round(subsibling_item['amount'] * bursary_amount, precision)

            subbursary_item = list(filter(lambda x: x['id'] == student_id, subbursaries))[0]
            subbursary_item['amount'] += round(bursary_item['amount'] + subsibling_item['amount'], precision)

            discount_item = list(filter(lambda x: x['id'] == student_id, discounts))[0]
            discount_item['amount'] += round(subbursary_item['amount'] * discount_amount, precision)

            total_item = list(filter(lambda x: x['id'] == student_id, totals))[0]
            total_item['amount'] += round(discount_item['amount'] + subbursary_item['amount'], precision)

        amount = 0
        for payment in payments:
            for i in payment['amount']:
                amount += i['amount']
            payment['amount'].append({'id': 0, 'amount': amount})

        amount = 0
        for bursary in bursaries:
            for i in bursary['amount']:
                amount += i['amount']
            bursary['amount'].append({'id': 0, 'amount': amount})
        if amount == 0:
            bursaries = False

        amount = 0
        for i in siblings:
            amount += i['amount']
        siblings.append({'id': 0, 'amount': amount})
        if amount == 0:
            siblings = False

        amount = 0
        for i in discounts:
            amount += i['amount']
        discounts.append({'id': 0, 'amount': amount})

        amount = 0
        for i in subpayments:
            amount += i['amount']
        subpayments.append({'id': 0, 'amount': amount})

        amount = 0
        for i in subsiblings:
            amount += i['amount']
        subsiblings.append({'id': 0, 'amount': amount})

        amount = 0
        for i in subbursaries:
            amount += i['amount']
        subbursaries.append({'id': 0, 'amount': amount})

        amount = 0
        for i in totals:
            amount += i['amount']
        totals.append({'id': 0, 'amount': amount})

        return {
            'students': students,
            'payments': payments,
            'bursaries': bursaries,
            'siblings': siblings,
            'discounts': discounts,
            'subpayments': subpayments,
            'subsiblings': subsiblings,
            'subbursaries': subbursaries,
            'totals': totals,
            'advance_discount': advance_discount,
            'sibling_discount': sibling_discount,
            'has_payment': len(list(filter(lambda x: x != 0, payment_ids))) > 1,
            'has_bursary': len(list(filter(lambda x: x != 0, bursary_ids))) > 0,
            'currency': currency,
        }

class Partner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner','portal.mixin']

    def _compute_payment(self):
        for partner in self:
            if partner.parent_id:
                partner.payable_count = len(partner.parent_id.payment_ids)
                partner.paid_count = len(partner.parent_id.paid_ids)
            else:
                partner.payable_count = len(partner.payment_ids)
                partner.paid_count = len(partner.paid_ids)

    @api.onchange('parent_id')
    def _compute_sibling(self):
        for partner in self:
            if partner.parent_id:
                partner.sibling_ids = partner.parent_id.child_ids.filtered(lambda x: x.id != partner.id)
            else:
                partner.sibling_ids = False

    @api.depends('child_ids.school_id')
    def _compute_schools(self):
        for partner in self:
            if partner.parent_id:
                partner.school_ids = False
            else:
                partner.school_ids = [(6, 0, partner.mapped('child_ids.school_id').ids)]

    is_sps = fields.Boolean(string='Payment System Member')
    school_id = fields.Many2one('res.student.school', ondelete='restrict')
    class_id = fields.Many2one('res.student.class', ondelete='restrict')
    bursary_id = fields.Many2one('res.student.bursary', ondelete='restrict')
    sibling_ids = fields.One2many('res.partner', compute='_compute_sibling')
    payment_ids = fields.One2many('res.student.payment', 'parent_id', string='Payment Items', copy=False, domain=[('paid','=',False)])
    paid_ids = fields.One2many('res.student.payment', 'parent_id', string='Paid Items', copy=False, domain=[('paid','!=',False)])
    paid_count = fields.Integer(string='Items Paid', compute='_compute_payment')
    payable_count = fields.Integer(string='Items To Pay', compute='_compute_payment')
    school_ids = fields.Many2many('res.student.school', string='Schools', compute='_compute_schools', store=True, readonly=True)
    date_email_sent = fields.Datetime('Email Sent Date', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['company_id'] = self.env.company.id
        langs = self.env['res.lang'].get_installed()
        for lang in langs:
            if lang[0] == 'tr_TR':
                res['lang'] = 'tr_TR'
                break
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if self._context.get('is_parent'):
            if view_type == 'form':
                view_id = self.env.ref('payment_student.parent_form').id
            else:
                view_id = self.env.ref('payment_student.parent_tree').id
        elif self._context.get('is_student'):
            if view_type == 'form':
                view_id = self.env.ref('payment_student.student_form').id
            else:
                view_id = self.env.ref('payment_student.student_tree').id
        return super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

    @api.model
    def create(self, vals):
        if 'school_id' in vals:
            vals['is_sps'] = True
        res = super().create(vals)
        for student in res:
            if student.is_sps and student.parent_id:
                templates = self.env['res.student.payment.template'].search([
                    ('school_id','=',student.school_id.id),
                    '|', ('class_id','=',student.class_id.id), ('class_id','=',False),
                    ('company_id','=',student.company_id.id),
                ])
                if templates:
                    val = []
                    for template in templates:
                        val.append({
                            'student_id': student.id,
                            'term_id': template.term_id.id,
                            'payment_type_id': template.payment_type_id.id,
                            'amount': template.amount,
                            'company_id': student.company_id.id,
                        })
                    self.env['res.student.payment'].sudo().create(val)
        return res

    def _get_name(self):
        partner = self
        name = partner.name or ''
        if self._context.get('show_address'):
            email = partner.email or _('No email')
            mobile = partner.mobile or _('No mobile')
            name = ' | '.join([name, email, mobile])
        return name

    def _compute_access_url(self):
        for rec in self:
            rec.access_url = '/p/%s/%s' % (rec.id, rec.access_token)

    def _get_share_url(self, redirect=False, signup_partner=False, pid=None):
        self.ensure_one()
        self._portal_ensure_token()
        return self.access_url

    def _get_payment_url(self):
        self.ensure_one()
        website = self.env['website'].sudo().search([('company_id','=',self.company_id.id)])
        if not website:
            raise UserError(_('There isn\'t any website related to this partner\'s company'))
        return website.domain + self._get_share_url()

    def _get_payment_terms(self):
        self.ensure_one()
        payments = self.env['res.student.payment'].sudo().search([('parent_id','=',self.id),('paid','=',False)])
        if not payments:
            raise UserError(_('There isn\'t any payment item related to this partner'))
        return ', '.join(payments.mapped('term_id.name'))

    def _get_payment_company(self):
        self.ensure_one()
        return self.company_id and self.company_id.name or self.env.company.name

    def _get_setting_line(self):
        self.ensure_one()
        settings = self.env['res.student.setting'].sudo().get_settings(company=self.company_id)
        if not settings:
            raise UserError(_('There isn\'t any payment settings related to this partner'))
        line = settings._get_setting_line()
        if line:
            month = line.date_start.strftime('%B')
            return {'month': month, 'installment': line.installment, 'percentage': line.percentage}
        return False

    def action_payable(self):
        self.ensure_one()
        action = self.env.ref('payment_student.action_payment').sudo().read()[0]
        if self.parent_id:
            action['domain'] = [('student_id', '=', self.id)]
            action['context'] = {'default_student_id': self.id, 'search_default_filterby_payable': True, 'domain': self.ids}
        else:
            action['domain'] = [('parent_id', '=', self.id)]
            action['context'] = {'domain': self.child_ids.ids, 'search_default_filterby_payable': True}
        return action

    def action_paid(self):
        self.ensure_one()
        action = self.env.ref('payment_student.action_payment').sudo().read()[0]
        if self.parent_id:
            action['domain'] = [('student_id', '=', self.id)]
            action['context'] = {'default_student_id': self.id, 'search_default_filterby_paid': True, 'domain': self.ids, 'create': False, 'edit': False, 'delete': False}
        else:
            action['domain'] = [('parent_id', '=', self.id)]
            action['context'] = {'domain': self.child_ids.ids, 'search_default_filterby_paid': True, 'create': False, 'edit': False, 'delete': False}
        return action

    def action_share_payment_link(self):
        self.ensure_one()
        action = self.sudo().env.ref('payment_student.parent_share').sudo().read()[0]
        return action

    def action_send(self):
        for rec in self:
            if len(rec.payment_ids):
                template = self.env['mail.template'].sudo().search([('company_id','=',rec.company_id.id)], limit=1)
                if template:
                    rec.with_context(force_send=True).message_post_with_template(template.id, composition_mode='comment')
                    rec.date_email_sent = datetime.now()

    @api.constrains('vat', 'email')
    def _check_partner_vals(self):
        for line in self:
            if line.vat:
                student = self.search([('id','!=',self.id),('vat','=',line.vat)], limit=1)
                if student:
                    raise UserError(_('There is already a student with the same Vat Number - %s') % student.name)
            if line.email and line.company_id:
                parent = self.search([('id','!=',self.id),('email','=',line.email),('company_id','=',line.company_id.id)], limit=1)
                if parent:
                    raise UserError(_('There is already a parent with the same email - %s') % parent.name)

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        mods = super(IrHttp, cls)._get_translation_frontend_modules_name()
        return mods + ['payment_student']
