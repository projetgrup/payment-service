from odoo import fields, models

class PaymentSettings(models.TransientModel):
    _inherit = 'payment.settings'

    installment_show_monthly = fields.Boolean(
        string='Show Monthly Price Column on Installments',
        config_parameter='paylox.installment.show_monthly',
        default=True,
    )
    conveyance_show_link = fields.Boolean(string='Enable Conveyance Document Show Link', related='company_id.conveyance_show_link', readonly=False)
    broker_registration_enabled = fields.Boolean('Enable Broker Registration', related='company_id.broker_registration_enabled', readonly=False)
    dealer_registration_enabled = fields.Boolean('Enable Dealer Registration', related='company_id.dealer_registration_enabled', readonly=False)
    escrow_insurance_quote_enabled = fields.Boolean('Enable Insurance Quote', related='company_id.escrow_insurance_quote_enabled', readonly=False)
    escrow_chain_ids = fields.One2many(related='company_id.escrow_chain_ids', readonly=False)
    escrow_broker_link_validity = fields.Integer(
        string='Broker Payment Link Validity (Minutes)',
        related='company_id.escrow_broker_link_validity',
        readonly=False,
        help='Duration in minutes for which broker payment links remain valid. Default is 15 minutes.'
    )
    paylox_escrow_split_ok = fields.Boolean('Split Escrow Items', related='company_id.paylox_escrow_split_ok', readonly=False)
    paylox_escrow_use_paid_price = fields.Boolean('Use Paid Price for Seller Amount', related='company_id.paylox_escrow_use_paid_price', readonly=False)
    escrow_provision_mode = fields.Boolean('Provisioned Transaction Mode', related='company_id.escrow_provision_mode', readonly=False)
