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

    def _get_escrow_chain_children(self, child_type):
        self.ensure_one()
        if self.system != 'escrow' or not child_type:
            return []
        chains = self.escrow_chain_ids.filtered(lambda c: c.active and c.child_type == child_type)
        return chains.mapped('child_type')

    def _get_escrow_allowed_types_for_user(self, user):
        self.ensure_one()
        if self.system != 'escrow' or not user:
            return set()

        allowed = set(ESCROW_DEFAULT_VISIBLE_TYPES)
        chains = self.escrow_chain_ids.filtered(lambda c: c.active and user in c.viewer_ids)
        allowed.update(chains.mapped('child_type'))
        return allowed
