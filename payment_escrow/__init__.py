# -*- coding: utf-8 -*-
from odoo.addons.payment_jetcheckout_system import SYSTEMS
SYSTEMS.append(('escrow', 'Escrow Payment System'))

from . import models
from . import controllers
from . import wizards
from .hooks import post_init_hook

