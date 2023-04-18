# -*- coding: utf-8 -*-
from odoo import models


class IrRule(models.Model):
    _inherit = 'ir.rule'

    def _get_rules(self, model_name, mode='read'):
       res = super()._get_rules(model_name, mode=mode)
       if self.env.user.has_group('payment_jetcheckout_system.group_system_own_partner'):
            rules = self.env.ref('base.res_partner_rule_private_employee') | self.env.ref('base.res_partner_rule_private_group')
            return res - rules
       return res
