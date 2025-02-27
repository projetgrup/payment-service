# -*- coding: utf-8 -*-
from odoo.addons.payment_jetcheckout_system import SYSTEMS
SYSTEMS.append(('vendor', 'Vendor Payment System'))

from . import models
from . import controllers
