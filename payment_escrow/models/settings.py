from odoo import fields, models

class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    installment_show_monthly = fields.Boolean(
        string='Show Monthly Price Column on Installments',
        config_parameter='paylox.installment.show_monthly',
        default=True,
    )
    conveyance_show_link = fields.Boolean(string='Enable Conveyance Document Show Link', related='company_id.conveyance_show_link', readonly=False)
