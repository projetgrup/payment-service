# -*- coding: utf-8 -*-
from . import models
from . import controllers
from . import wizards
from . import report

from odoo.addons.payment import reset_payment_acquirer


def uninstall_hook(cr, registry):
    reset_payment_acquirer(cr, registry, 'jetcheckout')
