# -*- coding: utf-8 -*-

from odoo import fields, models, _


class PaymentSubscriptionStage(models.Model):
    _name = 'payment.subscription.stage'
    _description = 'Payment Subscription Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(
        string='Requirements', translate=True,
        help='Enter here the internal requirements for this stage. It will appear as a tooltip over the stage\'s name.'
    )
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='This stage is folded in the kanban view when there are not records in that stage to display.'
    )
    rating_template_id = fields.Many2one('mail.template',
        string='Rating Email Template',
        help='Send an email to the customer when the subscription is moved to this stage.',
        domain=[('model', '=', 'payment.subscription')],
    )
    in_progress = fields.Boolean(string='In Progress', default=True)
