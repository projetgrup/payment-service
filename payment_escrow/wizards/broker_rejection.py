# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BrokerRejectionWizard(models.TransientModel):
    _name = 'broker.rejection.wizard'
    _description = 'Broker Rejection Wizard'

    broker_id = fields.Many2one('res.partner', string='Broker', required=True)
    rejection_reason = fields.Text(string='Rejection Reason', required=True)

    def action_reject_broker(self):
        """Reject the broker and send notification"""
        self.ensure_one()
        
        if not self.broker_id or self.broker_id.paylox_escrow_type != 'broker':
            raise UserError(_('Invalid broker selected.'))
        
        self.broker_id.write({
            'broker_state': 'rejected',
            'broker_rejection_reason': self.rejection_reason,
        })
        
        # Send rejection notification
        self.broker_id._send_broker_rejection_notification()
        
        return {'type': 'ir.actions.act_window_close'}
