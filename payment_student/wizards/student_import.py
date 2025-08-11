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

            domain = []
            school = self.env['res.student.school']
            if line.student_school_name:
                domain.append(('name', '=', line.student_school_name))
            if line.student_school_code:
                domain.append(('code', '=', line.student_school_code))
            if domain:
                school = school.search(domain + [('company_id', '=', company.id)], limit=1)
                if not school:
                    #raise ValidationError(_('No school found with code "%s" for student "%s"') % (line.student_school_name, line.student_name))
                    school = school.create({
                        'name': line.student_school_name or line.student_school_code,
                        'code': line.student_school_code,
                        'company_id': company.id,
                    })

            domain = []
            bursary = self.env['res.student.bursary']
            if line.student_bursary_name:
                domain.append(('name', '=', line.student_bursary_name))
            if line.student_bursary_code:
                domain.append(('code', '=', line.student_bursary_code))
            if domain:
                bursary = bursary.search(domain + [('company_id', '=', company.id)], limit=1)
                if not bursary:
                    #raise ValidationError(_('No bursary found with code "%s" for student "%s"') % (line.student_bursary_name, line.student_name))
                    bursary = bursary.create({
                        'name': line.student_bursary_name or line.student_bursary_code,
                        'code': line.student_bursary_code,
                        'company_id': company.id,
                    })

            domain = []
            classroom = self.env['res.student.class']
            if line.student_class_name:
                domain.append(('name', '=', line.student_class_name))
            if line.student_class_code:
                domain.append(('code', '=', line.student_class_code))
            if domain:
                classroom = classroom.search(domain + [('company_id', '=', company.id)], limit=1)
                if not classroom:
                    #raise ValidationError(_('No classroom found with code "%s" for student "%s"') % (line.student_class_name, line.student_name))
                    classroom = classroom.create({
                        'name': line.student_class_name or line.student_class_code,
                        'code': line.student_class_code,
                        'company_id': company.id,
                    })

            domain = []
            campus = self.env['res.student.campus']
            if line.student_campus_name:
                domain.append(('name', '=', line.student_campus_name))
            if line.student_campus_code:
                domain.append(('code', '=', line.student_campus_code))
            if domain:
                campus = campus.search(domain + [('company_id', '=', company.id)], limit=1)
                if not campus:
                    #raise ValidationError(_('No campus found with code "%s" for student "%s"') % (line.student_campus_name, line.student_name))
                    campus = campus.create({
                        'name': line.student_campus_name or line.student_campus_code,
                        'code': line.student_campus_code,
                        'company_id': company.id,
                    })

            domain = []
            faculty = self.env['res.student.faculty']
            if line.student_faculty_name:
                domain.append(('name', '=', line.student_faculty_name))
            if line.student_faculty_code:
                domain.append(('code', '=', line.student_faculty_code))
            if domain:
                faculty = faculty.search(domain + [('company_id', '=', company.id)], limit=1)
                if not faculty:
                    #raise ValidationError(_('No faculty found with code "%s" for student "%s"') % (line.student_faculty_name, line.student_name))
                    faculty = faculty.create({
                        'name': line.student_faculty_name or line.student_faculty_code,
                        'code': line.student_faculty_code,
                        'company_id': company.id,
                    })

            domain = []
            department = self.env['res.student.department']
            if line.student_department_name:
                domain.append(('name', '=', line.student_department_name))
            if line.student_department_code:
                domain.append(('code', '=', line.student_department_code))
            if domain:
                department = department.search(domain + [('company_id', '=', company.id)], limit=1)
                if not department:
                    #raise ValidationError(_('No department found with code "%s" for student "%s"') % (line.student_department_name, line.student_name))
                    department = department.create({
                        'name': line.student_department_name or line.student_department_code,
                        'code': line.student_department_code,
                        'company_id': company.id,
                    })

            domain = []
            program = self.env['res.student.program']
            if line.student_program_name:
                domain.append(('name', '=', line.student_program_name))
            if line.student_program_code:
                domain.append(('code', '=', line.student_program_code))
            if domain:
                program = program.search(domain + [('company_id', '=', company.id)], limit=1)
                if not program:
                    #raise ValidationError(_('No program found with code "%s" for student "%s"') % (line.student_program_name, line.student_name))
                    program = program.create({
                        'name': line.student_program_name or line.student_program_code,
                        'code': line.student_program_code,
                        'company_id': company.id,
                    })

            domain = []
            term = self.env['res.student.term']
            if line.student_term_name:
                domain.append(('name', '=', line.student_term_name))
            if line.student_term_code:
                domain.append(('code', '=', line.student_term_code))
            if domain:
                term = term.search(domain + [('company_id', '=', company.id)], limit=1)
                if not term:
                    #raise ValidationError(_('No term found with code "%s" for student "%s"') % (line.student_term, line.student_name))
                    term = term.create({
                        'name': line.student_term_name or line.student_term_code,
                        'code': line.student_term_code,
                        'company_id': company.id,
                    })
                context.update({'term_id': term.id})

            if line.parent_campaign:
                acquirers = self.env['payment.acquirer'].sudo()._get_acquirer(company=self.env.company, providers=['jetcheckout'], raise_exception=False)
                campaign = self.env['payment.acquirer.jetcheckout.campaign'].sudo().search([
                    ('acquirer_id', 'in', acquirers.ids),
                    ('name', '=', line.parent_campaign),
                ], limit=1)
                if not campaign:
                    raise ValidationError(_('No campaign found with name "%s" for parent "%s"') % (line.student_class, line.parent_name))
                context.update({'campaign_id': campaign.id})

            if self.env.context.get('active_subsystem') in ('student_university',):
                context.update({'skip_student_vat_check': True})

            students = self.env['res.partner'].with_context({'no_vat_validation': True, 'active_system': 'student'}).sudo().with_context(**context)
            student = students.search([
                ('company_id', '=', company.id),
                ('vat', '=', line.student_vat)
            ])
            if len(student) > 1:
                if self.env.context.get('active_subsystem') not in ('student_university',):
                    raise ValidationError(_('There is more than one student with the same characteristics in the records. Please contact the system administrator.\n\n⸻ Details ⸻\nVAT: %s') % line.student_vat)
                else:
                    student = student[0]

            values = {
                'name': line.student_name,
                'vat': line.student_vat,
                'ref': line.student_ref,
                'email': line.student_email,
                'phone': line.student_phone,
                'mobile': line.student_phone,
                'school_id': school.id,
                'bursary_id': bursary.id,
                'class_id': classroom.id,
                'system_student_campus_id': campus.id,
                'system_student_faculty_id': faculty.id,
                'system_student_department_id': department.id,
                'system_student_program_id': program.id,
                'company_id': company.id,
                'system': 'student',
                'is_company': False,
            }
            if self.env.context.get('active_subsystem') not in ('student_university',):
                parent = self.env['res.partner'].sudo().search([
                    ('company_id', '=', company.id),
                    ('email', '=', line.parent_email)
                ], limit=1)
                if not parent:
                    parent = self.env['res.partner'].sudo().create({
                        'name': line.parent_name,
                        'email': line.parent_email,
                        'phone': line.parent_phone,
                        'mobile': line.parent_phone,
                        'company_id': company.id,
                        'system': 'student',
                        'is_company': True,
                        'parent_id': False,
                    })
                values.update({
                    'parent_id': parent.id,
                })
            if student:
                student.write(values)
            else:
                student = students.create(values)

            types = []
            vals = {}
            send = True
            if company.api_item_notif_mail_create_ok:
                template = company.api_item_notif_mail_create_template
                if template:
                    if company.api_item_notif_mail_create_filter_email:
                        parent_email = parent.email
                        emails = company.api_item_notif_mail_create_filter_email.split('\n')
                        if company.api_item_notif_mail_create_filter_email_ok and all(email not in parent_email for email in emails):
                            send = False
                        elif not company.api_item_notif_mail_create_filter_email_ok and any(email in parent_email for email in emails):
                            send = False
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_email').id)
                    vals.update({'mail_template_id': template.id})
            if company.api_item_notif_sms_create_ok:
                template = company.api_item_notif_sms_create_template
                if template:
                    if company.api_item_notif_sms_create_filter_number:
                        parent_number = parent.mobile.replace(' ', '')
                        numbers = company.api_item_notif_sms_create_filter_number.split('\n')
                        if company.api_item_notif_sms_create_filter_number_ok and all(number not in parent_number for number in numbers):
                            send = False
                        elif not company.api_item_notif_sms_create_filter_number_ok and any(number in parent_number for number in numbers):
                            send = False
                    types.append(self.env.ref('payment_jetcheckout_system.send_type_sms').id)
                    vals.update({'sms_template_id': template.id})
            if send and types:
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

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class PaymentStudentImportLine(models.TransientModel):
    _name = 'payment.student.import.line'
    _description = 'Payment Student Import Line'

    wizard_id = fields.Many2one('payment.student.import')
    student_name = fields.Char('Name', readonly=True, required=True)
    student_email = fields.Char('Email', readonly=True)
    student_phone = fields.Char('Phone', readonly=True)
    student_vat = fields.Char('VAT', readonly=True, required=True)
    student_ref = fields.Char('Reference', readonly=True)
    student_school_name = fields.Char('School Name', readonly=True)
    student_school_code = fields.Char('School Code', readonly=True)
    student_class_name = fields.Char('Class Name', readonly=True)
    student_class_code = fields.Char('Class Code', readonly=True)
    student_bursary_name = fields.Char('Bursary Name', readonly=True)
    student_bursary_code = fields.Char('Bursary Code', readonly=True)
    student_term_name = fields.Char('Term Name', readonly=True)
    student_term_code = fields.Char('Term Code', readonly=True)
    student_campus_name = fields.Char('Campus Name', readonly=True)
    student_campus_code = fields.Char('Campus Code', readonly=True)
    student_faculty_name = fields.Char('Faculty Name', readonly=True)
    student_faculty_code = fields.Char('Faculty Code', readonly=True)
    student_department_name = fields.Char('Department Name', readonly=True)
    student_department_code = fields.Char('Department Code', readonly=True)
    student_program_name = fields.Char('Program Name', readonly=True)
    student_program_code = fields.Char('Program Code', readonly=True)
    parent_name = fields.Char('Parent Name', readonly=True)
    parent_email = fields.Char('Parent Email', readonly=True)
    parent_phone = fields.Char('Parent Phone', readonly=True)
    parent_campaign = fields.Char('Campaign', readonly=True)
