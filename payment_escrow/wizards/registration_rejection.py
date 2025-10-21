# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RegistrationRejectionWizard(models.TransientModel):
    _name = 'registration.rejection.wizard'
    _description = 'Registration Rejection Wizard'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject_registration(self):
        """Reject the registration and send notification"""
        self.ensure_one()

        if not self.partner_id or self.partner_id.paylox_escrow_type != 'broker' and self.partner_id.paylox_escrow_type != 'dealer':
            raise UserError(_('Invalid partner selected.'))

        self.partner_id.write({
            'approval_state': 'rejected',
            'rejection_reason': self.rejection_reason,
        })
        
        # Send rejection notification
        self.partner_id._send_partner_rejection_notification()
        
        return {'type': 'ir.actions.act_window_close'}
