# -*- coding: utf-8 -*-
from odoo import fields, models

from .approval_chain import ESCROW_DEFAULT_VISIBLE_TYPES


class ResCompany(models.Model):
    _inherit = 'res.company'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])
    conveyance_show_link = fields.Boolean(string='Enable Conveyance Document Show Link', default=False)
    broker_registration_enabled = fields.Boolean('Enable Broker Registration', default=False)
    dealer_registration_enabled = fields.Boolean('Enable Dealer Registration', default=False)
    escrow_insurance_quote_enabled = fields.Boolean('Enable Insurance Quote', default=False)
    escrow_chain_ids = fields.One2many('escrow.approval.chain', 'company_id', string='Escrow Approval Chains')
    escrow_broker_link_validity = fields.Integer(
        string='Broker Payment Link Validity (Minutes)',
        default=15,
        help='Duration in minutes for which broker payment links remain valid. Default is 15 minutes.'
    )
    paylox_escrow_split_ok = fields.Boolean('Split Escrow Items', default=False)
    paylox_escrow_use_paid_price = fields.Boolean('Use Paid Price for Seller Amount', default=True)
    escrow_provision_mode = fields.Boolean('Provisioned Transaction Mode', default=False, help="If enabled, allows proceeding to next steps even if seller verification fails (provision mode).")

    def _get_escrow_chain_children(self, parent_type):
        self.ensure_one()
        if self.system != 'escrow' or not parent_type:
            return []
        chains = self.escrow_chain_ids.filtered(lambda c: c.parent_type == parent_type)
        return chains.mapped('child_type')

    def _get_escrow_allowed_types_for_user(self, user):
        self.ensure_one()
        if self.system != 'escrow' or not user:
            return set()

        allowed = set(ESCROW_DEFAULT_VISIBLE_TYPES)
        chains = self.escrow_chain_ids.filtered(lambda c: c.active and user in c.viewer_ids)
        allowed.update(chains.mapped('child_type'))
        return allowed
