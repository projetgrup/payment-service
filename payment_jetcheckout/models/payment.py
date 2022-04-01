# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError, ValidationError
import base64

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _prepare_jetcheckout_payment_moves(self, line, commission):
        all_move_vals = []
        line = line.with_context(force_company=line.company_id.id)
        for payment in self:
            payment = payment.with_context(force_company=payment.journal_id.company_id.id)
            company_currency = payment.company_id.currency_id
            amount = payment.amount

            partner_id = payment.partner_id.commercial_partner_id

            if payment.currency_id == company_currency:
                balance = amount
                commission_balance = commission
                amount = 0.0
                commission = 0.0
                currency_id = False
            else:
                balance = payment.currency_id._convert(amount, company_currency, payment.company_id, payment.payment_date)
                commission_balance = payment.currency_id._convert(commission_balance, company_currency, payment.company_id, payment.payment_date)
                currency_id = payment.currency_id.id

            journal_debit_account_id = payment.journal_id.default_debit_account_id
            if not journal_debit_account_id:
                raise ValidationError(_('Journal debit account missing'))
            journal_credit_account_id = payment.journal_id.default_credit_account_id
            if not journal_credit_account_id:
                raise ValidationError(_('Journal credit account missing'))
            partner_payable_account_id = line.partner_id.property_account_payable_id
            if not partner_payable_account_id:
                raise ValidationError(_('Partner payable account missing'))
            partner_receivable_account_id = partner_id.property_account_receivable_id
            if not partner_receivable_account_id:
                raise ValidationError(_('Partner receivable account missing'))

            move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'journal_id': payment.journal_id.id,
                'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                'line_ids': [
                    (0, 0, {
                        'display_type': False,
                        'name': payment.name,
                        'amount_currency': amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': balance,
                        'credit': 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': False,
                        'account_id': journal_debit_account_id.id,
                        'payment_id': payment.id,
                    }),
                    (0, 0, {
                        'display_type': False,
                        'name': payment.name,
                        'amount_currency': commission if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': commission_balance,
                        'credit': 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': line.partner_id.id,
                        'account_id': partner_payable_account_id.id,
                        'payment_id': payment.id,
                    }),
                    (0, 0, {
                        'display_type': False,
                        'name': payment.name,
                        'amount_currency': -amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': balance,
                        'date_maturity': payment.payment_date,
                        'partner_id': partner_id.id,
                        'account_id': partner_receivable_account_id.id,
                        'payment_id': payment.id,
                    }),
                    (0, 0, {
                        'display_type': False,
                        'name': payment.name,
                        'amount_currency': -commission if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': 0.0,
                        'credit': commission_balance,
                        'date_maturity': payment.payment_date,
                        'partner_id': False,
                        'account_id': journal_credit_account_id.id,
                        'payment_id': payment.id,
                    }),
                ],
            }
            all_move_vals.append(move_vals)
            return all_move_vals

    def post_with_jetcheckout(self, line, commission, provider_commission, ip_address):
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))
            if commission > 0:
                commission_product = self.env['product.product'].search([('default_code','=','JETCOM')], limit=1)
                if not commission_product:
                    commission_product = self.env['product.product'].create({
                        'name': _('Commission'),
                        'default_code': 'JETCOM',
                        'type': 'service',
                        'uom_id': self.env.ref('uom.product_uom_unit').id,
                        'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                        'categ_id': self.env.ref('product.cat_expense').id,
                        'purchase_ok': False,
                    })
            else:
                commission_product = False

            sequence_code = 'account.payment.customer.invoice'
            rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
            if not rec.name:
                raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
            try:
                moves = AccountMove.create(rec._prepare_jetcheckout_payment_moves(line, provider_commission))
            except Exception as e:
                raise ValidationError(str(e))
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})
            if rec.invoice_ids:
                (moves[0] + rec.invoice_ids).line_ids.filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id and not (line.account_id == line.payment_id.writeoff_account_id and line.name == line.payment_id.writeoff_label)).reconcile()

            IrConfig = self.env['ir.config_parameter'].sudo()
            base_url = IrConfig.get_param('report.url') or IrConfig.get_param('web.base.url')
            content = line.acquirer_id._render_jetcheckout_terms(rec.company_id, rec.partner_id)
            layout = self.env['ir.ui.view'].browse(self.env['ir.ui.view'].get_view_id('web.minimal_layout'))
            html = layout.render(dict(subst=True, body=content, base_url=base_url))
            pdf_content = self.env['ir.actions.report']._run_wkhtmltopdf(
                [html],
                specific_paperformat_args={'data-report-margin-top': 10, 'data-report-header-spacing': 10}
            )
            attachment = self.env['ir.attachment'].sudo().create({
                'name': _('Terms & Conditions.pdf'),
                'res_model': 'account.payment',
                'res_id': rec.id,
                'mimetype': 'application/pdf',
                'datas': base64.b64encode(pdf_content),
                'type': 'binary',
            })

            body = _('User has accepted Terms & Conditions. User IP Address is %s') % (ip_address,)
            rec.message_post(body=body, attachment_ids=attachment.ids)

            if commission_product:
                order_vals = {
                    'partner_id': rec.partner_id.id,
                    'order_line': [(0, 0, {
                        'product_id': commission_product.id,
                        'price_unit': commission
                    })]
                }
                order = self.env['sale.order'].sudo().create(order_vals)
                order.action_confirm()

                parameter = IrConfig.get_param('payment_jetcheckout.commission_invoice', 'no')
                if parameter == 'draft' or parameter == 'post':
                    moves = order._create_invoices()
                    if parameter == 'post':
                        moves.sudo().post()
        return True
