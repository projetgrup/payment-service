# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

ESCROW_TYPE_SELECTION = [
    ('platform_owner', 'Platform Owner'),
    ('infrastructure_provider', 'Infrastructure Provider'),
    ('broker', 'Broker'),
    ('owner', 'Owner'),
    ('customer', 'Customer'),
    ('dealer', 'Dealer'),
    ('card_holder', 'Card Holder'),
]

ESCROW_DEFAULT_VISIBLE_TYPES = {'owner', 'broker'}


class EscrowApprovalChain(models.Model):
    _name = 'escrow.approval.chain'
    _description = 'Escrow Approval Chain'
    _order = 'sequence, id'

    name = fields.Char(string='Description', compute='_compute_name', store=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    parent_type = fields.Selection(selection=ESCROW_TYPE_SELECTION, required=True)
    child_type = fields.Selection(selection=ESCROW_TYPE_SELECTION, required=True)
    viewer_ids = fields.Many2many(
        'res.users',
        'escrow_chain_user_rel',
        'chain_id',
        'user_id',
        string='Authorized Users',
        help='Users that can list transfer and transaction records for the automatic escrow type.',
    )

    _sql_constraints = [
        (
            'escrow_chain_unique',
            'unique(company_id, parent_type, child_type)',
            'Each parent escrow type can only be linked to a child type once per company.',
        ),
    ]

    @api.depends('parent_type', 'child_type')
    def _compute_name(self):
        labels = dict(ESCROW_TYPE_SELECTION)
        for chain in self:
            source = labels.get(chain.parent_type, chain.parent_type or '')
            target = labels.get(chain.child_type, chain.child_type or '')
            chain.name = '%s → %s' % (source, target) if source and target else ''

    @api.constrains('parent_type', 'child_type')
    def _check_types(self):
        for chain in self:
            if chain.parent_type and chain.parent_type == chain.child_type:
                raise ValidationError(_('Parent escrow type cannot match the child escrow type.'))

    def get_chain_map(self):
        mapping = defaultdict(list)
        for chain in self:
            mapping[chain.parent_type].append(chain.child_type)
        return mapping
