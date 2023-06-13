# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero
import base64

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        self.ensure_one()
        line = self.env.context.get('line')
        if not line:
            return super()._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

        journal_account_id = self.journal_id.default_account_id
        if not journal_account_id:
            raise ValidationError(_('Journal default account missing'))
        partner_payable_account_id = line.partner_id.property_account_payable_id
        if not partner_payable_account_id:
            raise ValidationError(_('Partner payable account missing'))
        partner_receivable_account_id = self.partner_id.property_account_receivable_id
        if not partner_receivable_account_id:
            raise ValidationError(_('Partner receivable account missing'))

        if self.payment_type == 'inbound':
            amount_currency = self.amount
            commission_currency = self.payment_transaction_id.jetcheckout_customer_amount
        elif self.payment_type == 'outbound':
            amount_currency = -self.amount
            commission_currency = -self.payment_transaction_id.jetcheckout_customer_amount
        else:
            amount_currency = 0.0
            commission_currency = 0.0

        balance = self.currency_id._convert(
            amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )

        commission_balance = self.currency_id._convert(
            commission_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )

        currency_id = self.currency_id.id
        liquidity_line_name = self.payment_reference
        payment_display_name = self._prepare_payment_display_name()
        default_line_name = self.env['account.move.line']._get_default_line_name(
            payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
            self.amount,
            self.currency_id,
            self.date,
            partner=self.partner_id,
        )

        lines = [{
            'name': liquidity_line_name or default_line_name,
            'date_maturity': self.date,
            'amount_currency': amount_currency,
            'currency_id': currency_id,
            'debit': balance if balance > 0.0 else 0.0,
            'credit': -balance if balance < 0.0 else 0.0,
            'partner_id': False,
            'account_id': journal_account_id.id,
        }, {
            'name': liquidity_line_name or default_line_name,
            'date_maturity': self.date,
            'amount_currency': amount_currency,
            'currency_id': currency_id,
            'debit': -balance if balance < 0.0 else 0.0,
            'credit': balance if balance > 0.0 else 0.0,
            'partner_id': self.partner_id.id,
            'account_id': partner_receivable_account_id.id,
        }]

        if not float_is_zero(commission_balance, precision_digits=currency_id.decimal_places):
            lines.insert(1, {
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': amount_currency,
                'currency_id': currency_id,
                'debit': commission_balance if commission_balance > 0.0 else 0.0,
                'credit': -commission_balance if commission_balance < 0.0 else 0.0,
                'partner_id': line.partner_id.id,
                'account_id': partner_payable_account_id.id,
            })
            lines.append({
                'name': liquidity_line_name or default_line_name,
                'date_maturity': self.date,
                'amount_currency': amount_currency,
                'currency_id': currency_id,
                'debit': -commission_balance if commission_balance < 0.0 else 0.0,
                'credit': commission_balance if commission_balance > 0.0 else 0.0,
                'partner_id': False,
                'account_id': journal_account_id.id,
            })

        return lines

    def post_with_jetcheckout(self, line, commission, ip_address):
        self.move_id._post(soft=False)
        if commission > 0:
            product = self.env.ref('payment_jetcheckout.product_commission')
            order_vals = {
                'partner_id': self.partner_id.id,
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'price_unit': commission
                })]
            }
            order = self.env['sale.order'].sudo().create(order_vals)
            order.action_confirm()

            parameter = self.env['ir.config_parameter'].sudo().get_param('payment_jetcheckout.commission_invoice', 'no')
            if parameter == 'draft' or parameter == 'post':
                moves = order._create_invoices()
                if parameter == 'post':
                    moves.sudo().action_post()

        if not self.env.context.get('no_terms'):
            self._generate_jetcheckout_terms(line, ip_address)
        return True

    def _generate_jetcheckout_terms(self, line, ip_address):
        icp = self.env['ir.config_parameter'].sudo()
        base_url = icp.get_param('report.url') or icp.get_param('web.base.url')
        acquirer = line.acquirer_id
        if acquirer.provider == 'jetcheckout' and not acquirer.jetcheckout_no_terms:
            body = line.acquirer_id._render_jetcheckout_terms(self.company_id.id, self.partner_id.id)
            layout = self.env.ref('payment_jetcheckout.report_layout')
            html = layout._render({'body': body, 'base_url': base_url})
            pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf(
                [html],
                specific_paperformat_args={'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            )
            attachment = self.env['ir.attachment'].sudo().create({
                'name': _('Terms & Conditions.pdf'),
                'res_model': 'account.payment',
                'res_id': self.id,
                'mimetype': 'application/pdf',
                'datas': base64.b64encode(pdf_content),
                'type': 'binary',
            })

            body = _('User has accepted Terms & Conditions. User IP Address is %s') % (ip_address,)
            self.message_post(body=body, attachment_ids=attachment.ids)
