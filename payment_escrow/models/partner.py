# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    system = fields.Selection(selection_add=[('escrow', 'Escrow Payment System')])

    def action_payable(self):
        action = super(Partner, self).action_payable()
        system = self.company_id and self.company_id.system or self.env.context.get('active_system')
        if system == 'escrow':
            action['context']['domain'] = self.ids
        return action

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if view_type == 'form' and self.env.context.get('form_view_ref'):
            view_id = self.env.ref(self.env.context['form_view_ref']).id
        elif view_type == 'tree' and self.env.context.get('tree_view_ref'):
            view_id = self.env.ref(self.env.context['tree_view_ref']).id
        elif view_type == 'kanban' and self.env.context.get('kanban_view_ref'):
            view_id = self.env.ref(self.env.context['kanban_view_ref']).id
        elif view_type in ('form', 'tree', 'kanban'):
            system = self.env.context.get('active_system') or self.env.context.get('system')
            if system == 'escrow':
                type = self.env.context.get('active_escrow_type', '')
                try:
                    view_id = self.env.ref('payment_escrow.%s_%s' % (view_type, type)).id
                except:
                    raise UserError(_('View cannot be found'))
                self = self.with_context(skip_view_mapping=True)
        return super(Partner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
