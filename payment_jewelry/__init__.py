# -*- coding: utf-8 -*-
from odoo.addons.payment_jetcheckout_system import SYSTEMS
SYSTEMS.append(('jewelry', 'Jewelry Payment System'))

from . import controllers
from . import models
