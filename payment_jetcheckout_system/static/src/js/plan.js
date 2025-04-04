/** @odoo-module alias=paylox.token.verify.page **/
'use strict';

import { _t } from 'web.core';
import publicWidget from 'web.public.widget';

publicWidget.registry.payloxPlanResult = publicWidget.Widget.extend({
    selector: '.payment-plan-result #wrapwrap',

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            setTimeout(() => {
                if (document.getElementById('success')) {
                    window.parent.document.querySelector('.o_form_payment_plan_pay').closest('.modal-content').querySelector('header button.close').click();
                }
            }, 2000);
        });
    },
});

export default publicWidget.registry.payloxTokenVerify;