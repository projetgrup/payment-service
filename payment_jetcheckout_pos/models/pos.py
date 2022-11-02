# -*- coding: utf-8 -*-
import random
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_vpos = fields.Boolean(string='Virtual PoS', copy=False)
