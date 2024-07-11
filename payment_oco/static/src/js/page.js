/** @odoo-module alias=paylox.system.oco **/
'use strict';

import publicWidget from 'web.public.widget';
import systemPage from 'paylox.system.page';

publicWidget.registry.payloxSystemOco = systemPage.extend({
    selector: '.payment-oco #wrapwrap',
});
