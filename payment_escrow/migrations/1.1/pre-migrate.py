# -*- coding: utf-8 -*-
from odoo.tools.sql import column_exists

def migrate(cr, version):
    """
    Migration script to add broker-related fields to res_partner table
    """
    
    # Broker text fields
    if not column_exists(cr, 'res_partner', 'broker_sign_name'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_sign_name varchar')
    
    if not column_exists(cr, 'res_partner', 'broker_authorized_person'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_authorized_person varchar')
    
    # Broker state field with default value
    if not column_exists(cr, 'res_partner', 'broker_state'):
        cr.execute("ALTER TABLE res_partner ADD COLUMN broker_state varchar DEFAULT 'draft'")
    
    # Broker binary fields for documents (stored as bytea in PostgreSQL)
    if not column_exists(cr, 'res_partner', 'broker_tax_plate'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_tax_plate bytea')
    
    if not column_exists(cr, 'res_partner', 'broker_tax_plate_filename'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_tax_plate_filename varchar')
    
    if not column_exists(cr, 'res_partner', 'broker_signature_circular'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_signature_circular bytea')
    
    if not column_exists(cr, 'res_partner', 'broker_signature_circular_filename'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_signature_circular_filename varchar')
    
    if not column_exists(cr, 'res_partner', 'broker_identity_doc'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_identity_doc bytea')
    
    if not column_exists(cr, 'res_partner', 'broker_identity_doc_filename'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_identity_doc_filename varchar')
    
    if not column_exists(cr, 'res_partner', 'broker_authorization_doc'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_authorization_doc bytea')
    
    if not column_exists(cr, 'res_partner', 'broker_authorization_doc_filename'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_authorization_doc_filename varchar')
    
    if not column_exists(cr, 'res_partner', 'broker_contract'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_contract bytea')
    
    if not column_exists(cr, 'res_partner', 'broker_contract_filename'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_contract_filename varchar')
    
    # Broker approval fields
    if not column_exists(cr, 'res_partner', 'broker_approval_date'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_approval_date timestamp')
    
    if not column_exists(cr, 'res_partner', 'broker_approved_by'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_approved_by integer REFERENCES res_users(id) ON DELETE SET NULL')
    
    if not column_exists(cr, 'res_partner', 'broker_rejection_reason'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_rejection_reason text')

    if not column_exists(cr, 'res_partner', 'broker_default_campaign_id'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_default_campaign_id integer')

    if not column_exists(cr, 'res_partner', 'broker_campaign_id'):
        cr.execute('ALTER TABLE res_partner ADD COLUMN broker_campaign_id integer')
