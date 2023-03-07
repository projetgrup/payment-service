# -*- coding: utf-8 -*-
import base64
import xlrd

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class PaymentStudentImport(models.TransientModel):
    _name = 'payment.student.import'
    _description = 'Payment Student Import'

    file = fields.Binary()
    filename = fields.Char()
    line_ids = fields.One2many('payment.student.import.line', 'wizard_id', 'Lines', readonly=True)

    def _get_header(self):
        header = {}
        for name, field in self.line_ids._fields.items():
            if field.type == 'char' and name.startswith(('student_', 'parent_')):
                header.update({
                    field._description_string(self.env): {
                        'name': name,
                        'required': field.required,
                        }
                    })
        return header

    @api.onchange('file')
    def onchange_file(self):
        if self.file:
            data = base64.b64decode(self.file)
            wb = xlrd.open_workbook(file_contents=data)
            sheet = wb.sheet_by_index(0)
            header = self._get_header()
            values = []
            cols = []
            for i in range(sheet.nrows):
                row = sheet.row_values(i)
                if not i:
                    for name, field in header.items():
                        if field['required'] and name not in row:
                            raise UserError(_('Please create "%s" column') % name)

                    for title in row:
                        if title in header:
                            cols.append(header[title]['name'])
                        else:
                            raise UserError(_('Column title "%s" is not supported') % title)
                else:
                    vals = []
                    for val in row:
                        try:
                            vals.append(str(int(val)))
                        except:
                            vals.append(val)
                    values.append(dict(zip(cols, vals)))
            self.line_ids = [(5, 0, 0)] + [(0, 0, value) for value in values]

        else:
            self.line_ids = [(5, 0, 0)]

    def confirm(self):
        context = {}
        company = self.env.company
        for line in self.line_ids:
            school = self.env['res.student.school'].search([
                ('company_id', '=', company.id),
                ('code', '=', line.student_school)
            ], limit=1)
            if not school:
                raise ValidationError(_('No school found with code "%s" for student "%s"') % (line.student_school, line.student_name))

            bursary = self.env['res.student.bursary']
            if line.student_bursary:
                bursary = bursary.search([
                    ('company_id', '=', company.id),
                    ('code', '=', line.student_bursary)
                ], limit=1)
                if not bursary:
                    raise ValidationError(_('No bursary found with code "%s" for student "%s"') % (line.student_bursary, line.student_name))                

            classroom = self.env['res.student.class'].search([
                ('company_id', '=', company.id),
                ('code', '=', line.student_class)
            ], limit=1)
            if not classroom:
                raise ValidationError(_('No classroom found with code "%s" for student "%s"') % (line.student_class, line.student_name))

            parent = self.env['res.partner'].sudo().search([
                ('company_id', '=', company.id),
                ('email', '=', line.parent_email)
            ], limit=1)
            if not parent:
                parent = self.env['res.partner'].sudo().create({
                    'name': line.parent_name,
                    'email': line.parent_email,
                    'mobile': line.parent_mobile,
                    'company_id': company.id,
                    'system': 'student',
                    'is_company': True,
                    'parent_id': False,
                })

            if line.parent_campaign:
                acquirers = self.env['payment.acquirer'].sudo()._get_acquirer(company=self.env.company, providers=['jetcheckout'], raise_exception=False)
                campaign = self.env['payment.acquirer.jetcheckout.campaign'].sudo().search([
                    ('acquirer_id', 'in', acquirers.ids),
                    ('name', '=', line.parent_campaign),
                ], limit=1)
                if not campaign:
                    raise ValidationError(_('No campaign found with name "%s" for parent "%s"') % (line.student_class, line.parent_name))
                parent.write({'campaign_id': campaign.id})

            if line.student_term:
                term = self.env['res.student.term'].search([
                    ('company_id', '=', company.id),
                    ('code', '=', student.student_term)
                ], limit=1)
                if not term:
                    raise ValidationError(_('No term found with code "%s" for student "%s"') % (line.student_term, line.student_name))
                context.update({'term_id': term.id})

            students = self.env['res.partner'].with_context({'no_vat_validation': True, 'active_system': 'student'}).sudo().with_context(**context)
            student = students.search([
                ('company_id', '=', company.id),
                ('ref', '=', line.student_ref),
                ('vat', '=', line.student_vat)
            ])
            if len(student) > 1:
                raise ValidationError(_('There is more than one student with the same characteristics in the records. Please contact the system administrator.'))

            values = {
                'name': line.student_name,
                'vat': line.student_vat,
                'ref': line.student_ref,
                'school_id': school.id,
                'bursary_id': bursary.id,
                'class_id': classroom.id,
                'parent_id': parent.id,
                'company_id': company.id,
                'system': 'student',
                'is_company': False,
            }
            if student:
                student.write(values)
            else:
                student = students.create(values)

            types = []
            vals = {}
            if company.api_item_notif_mail_create_ok:
                template = company.api_item_notif_mail_create_template
                if template:
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_email').id)
                    vals.update({'mail_template_id': template.id})
            if company.api_item_notif_sms_create_ok:
                template = company.api_item_notif_sms_create_template
                if template:
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_sms').id)
                    vals.update({'sms_template_id': template.id})

            if types:
                authorized = self.env.ref('payment_jetcheckout_system.categ_authorized')
                user = self.env['res.users'].sudo().search([
                    ('company_id', '=', company.id),
                    ('partner_id.category_id', 'in', [authorized.id])
                ], limit=1) or self.env.user
                sending = self.env['payment.acquirer.jetcheckout.send'].sudo().with_context(partners=parent).create({
                    'selection': [(6, 0, types)],
                    'type_ids': [(6, 0, types)],
                    'company_id': company.id,
                    **vals
                })
                sending.with_user(user).send()


class PaymentStudentImportLine(models.TransientModel):
    _name = 'payment.student.import.line'
    _description = 'Payment Student Import Line'

    wizard_id = fields.Many2one('payment.student.import')
    student_name = fields.Char('Student', readonly=True, required=True)
    student_vat = fields.Char('Vat', readonly=True, required=True)
    student_ref = fields.Char('Reference', readonly=True)
    student_school = fields.Char('School', readonly=True, required=True)
    student_class = fields.Char('Class', readonly=True, required=True)
    student_bursary = fields.Char('Bursary', readonly=True)
    student_term = fields.Char('Term', readonly=True)
    parent_name = fields.Char('Parent', readonly=True, required=True)
    parent_email = fields.Char('Email', readonly=True, required=True)
    parent_mobile = fields.Char('Mobile', readonly=True, required=True)
    parent_campaign = fields.Char('Campaign', readonly=True)

