# -*- coding: utf-8 -*-
from odoo import models, fields


class PayloxPartnerFollower(models.TransientModel):
    _name = 'paylox.partner.follower'
    _description = 'Partner Follower'

    follower_ids = fields.Many2many('res.partner', string='Followers')
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    def confirm(self):
        pids = self.env.context.get('active_ids')
        partners = self.env['res.partner'].browse(pids)
        for partner in partners:
            partner.message_subscribe(self.follower_ids.ids)
