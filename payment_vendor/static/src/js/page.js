/** @odoo-module alias=paylox.system.vendor **/
'use strict';

import publicWidget from 'web.public.widget';
import systemPage from 'paylox.system.page';

publicWidget.registry.payloxSystemVendor = systemPage.extend({
    selector: '.payment-vendor #wrapwrap',
});
