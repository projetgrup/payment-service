/** @odoo-module alias=paylox.system.product.flow **/
'use strict';

//import { _t } from 'web.core';
import systemFlow from 'paylox.system.page.flow';

systemFlow.dynamic.include({
    _onClickWelcomeNext: async function () {
        if (window.location.pathname.startsWith('/my/product')) {
            const overlay = this.wizard.page.overlay.$;
            const page = $('.payment-dynamic');
            overlay.css('opacity', '0');
            page.css('opacity', '0');
            setTimeout(() => overlay.remove(), 500);
            setTimeout(() => page.remove(), 500);
        } else {
            return this._super.apply(this, arguments);
        }
    }
});