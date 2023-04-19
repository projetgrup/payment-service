# -*- coding: utf-8 -*-
from odoo import models, fields


class PaymentItemWizard(models.TransientModel):
    _name = 'payment.item.wizard'
    _description = 'Payment Items Wizard'

    partner_id = fields.Many2one('res.partner', readonly=True)
    line_ids = fields.One2many('payment.item', related='partner_id.payable_ids', readonly=False)

    def write(self, values):
        res = super().write(values)
        if 'line_ids' in values:
            item = self.env['payment.item']
            for line in values['line_ids']:
                if line[0] == 0:
                    item.create(line[2])
                elif line[0] == 1:
                    item.write(line[2])
                elif line[0] == 2:
                    item.browse(line[1]).unlink()
        return res

    def confirm(self):
        return {
            'name': 'Payment Items',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '%s/p/%s' % (self.get_base_url(), self.partner_id._get_token())
        }
    
    def send(self):
        company = self.mapped('company_id') or self.env.company
        if len(company) > 1:
            raise Exception(_('Partners have to be in one company when sending mass messages, but there are %s of them. (%s)') % (len(company), ', '.join(company.mapped('name'))))

        type_email = self.env.ref('payment_jetcheckout_system.send_type_email')
        mail_template = self.env['mail.template'].sudo().search([('company_id', '=',company.id)], limit=1)
        sms_template = self.env['sms.template'].sudo().search([('company_id', '=', company.id)], limit=1)
        res = self.env['payment.acquirer.jetcheckout.send'].create({
            'selection': [(6, 0, type_email.ids)],
            'type_ids': [(6, 0, type_email.ids)],
            'mail_template_id': mail_template.id,
            'sms_template_id': sms_template.id,
            'company_id': company.id,
        })
        action = self.env.ref('payment_jetcheckout_system.action_system_send').sudo().read()[0]
        action['res_id'] = res.id
        return action
        return self.partner_id.action_send()
