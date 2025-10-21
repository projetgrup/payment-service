# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    if not column_exists(cr, 'res_partner', 'sign_name'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN sign_name varchar")
        cr.execute("UPDATE res_partner SET sign_name=broker_sign_name")
    if not column_exists(cr, 'res_partner', 'authorized_person'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN authorized_person varchar")
        cr.execute("UPDATE res_partner SET authorized_person=broker_authorized_person")
    if not column_exists(cr, 'res_partner', 'approval_state'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN approval_state varchar")
        cr.execute("UPDATE res_partner SET approval_state=broker_state")
    if not column_exists(cr, 'res_partner', 'tax_plate'):
        cr.execute("UPDATE ir_attachment SET name='tax_plate', res_field='tax_plate' WHERE res_field='broker_tax_plate'")
    if not column_exists(cr, 'res_partner', 'tax_plate_filename'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN tax_plate_filename varchar")
        cr.execute("UPDATE res_partner SET tax_plate_filename=broker_tax_plate_filename")
    if not column_exists(cr, 'res_partner', 'signature_circular'):
        cr.execute("UPDATE ir_attachment SET name='signature_circular', res_field='signature_circular' WHERE res_field='broker_signature_circular'")
    if not column_exists(cr, 'res_partner', 'signature_circular_filename'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN signature_circular_filename varchar")
        cr.execute("UPDATE res_partner SET signature_circular_filename=broker_signature_circular_filename")
    if not column_exists(cr, 'res_partner', 'identity_doc'):
        cr.execute("UPDATE ir_attachment SET name='identity_doc', res_field='identity_doc' WHERE res_field='broker_identity_doc'")
    if not column_exists(cr, 'res_partner', 'identity_doc_filename'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN identity_doc_filename varchar")
        cr.execute("UPDATE res_partner SET identity_doc_filename=broker_identity_doc_filename")
    if not column_exists(cr, 'res_partner', 'authorization_doc'):
        cr.execute("UPDATE ir_attachment SET name='authorization_doc', res_field='authorization_doc' WHERE res_field='broker_authorization_doc'")
    if not column_exists(cr, 'res_partner', 'authorization_doc_filename'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN authorization_doc_filename varchar")
        cr.execute("UPDATE res_partner SET authorization_doc_filename=broker_authorization_doc_filename")
    if not column_exists(cr, 'res_partner', 'contract_doc'):
        cr.execute("UPDATE ir_attachment SET name='contract_doc', res_field='contract_doc' WHERE res_field='broker_contract_doc'")
    if not column_exists(cr, 'res_partner', 'contract_doc_filename'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN contract_doc_filename varchar")
        cr.execute("UPDATE res_partner SET contract_doc_filename=broker_contract_doc_filename")
    if not column_exists(cr, 'res_partner', 'approval_date'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN approval_date timestamp")
        cr.execute("UPDATE res_partner SET approval_date=broker_approval_date")
    if not column_exists(cr, 'res_partner', 'approved_by'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN approved_by integer")
        cr.execute("UPDATE res_partner SET approved_by=broker_approved_by")
    if not column_exists(cr, 'res_partner', 'rejection_reason'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN rejection_reason text")
        cr.execute("UPDATE res_partner SET rejection_reason=broker_rejection_reason")
    if not column_exists(cr, 'res_partner', 'broker_dealer_id'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN broker_dealer_id integer")
    if not column_exists(cr, 'res_partner', 'dealer_referral_code'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN dealer_referral_code varchar")
    if not column_exists(cr, 'res_partner', 'dealer_broker_count'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN dealer_broker_count integer")
    if not column_exists(cr, 'res_company', 'dealer_registration_enabled'):
        cr.execute("ALTER TABLE res_company ADD COLUMN dealer_registration_enabled boolean")
