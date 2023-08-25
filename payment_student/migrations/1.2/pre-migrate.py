# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists


def migrate(cr, version):
    if not column_exists(cr, 'res_partner', 'system_student_faculty_id'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN system_student_faculty_id integer')

    if not column_exists(cr, 'res_partner', 'system_student_department_id'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN system_student_department_id integer')

    if not column_exists(cr, 'res_partner', 'system_student_program_id'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN system_student_program_id integer')
