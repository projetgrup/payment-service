# -*- coding: utf-8 -*-
from odoo.addons.payment_jetcheckout_system import SYSTEMS
SYSTEMS.append(('oco', 'Order Checkout'))

from . import models
from . import controllers
