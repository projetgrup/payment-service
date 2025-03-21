# -*- coding: utf-8 -*-
import logging
import traceback

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval, test_python_expr, json, pytz, datetime

logger = logging.getLogger(__name__)


class PaymentHook(models.Model):
    _name = 'payment.hook'
    _description = 'Payment Hooks'

    def _compute_name(self):
        for hook in self:
            hook.name = _('Hook #%s') % (hook.id or '?',)

    @api.depends('subtype')
    def _compute_subtype_transaction(self):
        for hook in self:
            hook.subtype_transaction = hook.subtype and hook.subtype.startswith('transaction') and hook.subtype

    def _set_subtype_transaction(self):
        for hook in self:
            hook.subtype = hook.subtype_transaction

    @api.depends('subtype')
    def _compute_subtype_item(self):
        for hook in self:
            hook.subtype_item = hook.subtype and hook.subtype.startswith('item') and hook.subtype

    def _set_subtype_item(self):
        for hook in self:
            hook.subtype = hook.subtype_item

    company_id = fields.Many2one('res.company', ondelete='cascade', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    name = fields.Char(compute='_compute_name')
    system = fields.Selection([])
    code = fields.Text()
    type = fields.Selection([
        ('transaction', 'Transaction'),
        ('item', 'Item'),
        ('route', 'Route'),
    ])
    subtype = fields.Selection([
        ('transaction_create', 'Creation'),
        ('transaction_authorize', 'Pre-Authorization'),
        ('transaction_finalize', 'Finalization'),
        ('transaction_cancel', 'Cancellation'),
        ('item_create', 'Creation'),
        ('item_finalize', 'Finalization'),
    ])
    subtype_transaction = fields.Selection([
        ('transaction_create', 'Creation'),
        ('transaction_authorize', 'Pre-Authorization'),
        ('transaction_finalize', 'Finalization'),
        ('transaction_cancel', 'Cancellation'),
    ], compute='_compute_subtype_transaction', inverse='_set_subtype_transaction')
    subtype_item = fields.Selection([
        ('item_create', 'Creation'),
        ('item_finalize', 'Finalization'),
    ], compute='_compute_subtype_item', inverse='_set_subtype_item')

    @api.constrains('code')
    def _check_code(self):
        for hook in self.sudo().filtered('code'):
            msg = test_python_expr(expr=hook.code.strip(), mode='exec')
            if msg:
                raise ValidationError(msg)

    def run(self, **kwargs):
        context = {
            'env': self.env,
            'datetime': datetime,
            'UserError': UserError,
            'logger': logger,
            'json': json,
            'pytz': pytz,
            **kwargs
        }
        try:
            for hook in self:
                safe_eval(hook.code.strip(), context, mode='exec', nocopy=True)
        except UserError:
            raise
        except:
            logger.error(traceback.format_exc())
            raise ValidationError(_('An error occured when triggering the hook.'))
