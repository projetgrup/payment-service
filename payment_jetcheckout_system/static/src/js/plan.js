/** @odoo-module alias=paylox.plan.pay.page **/
'use strict';

import { _t } from 'web.core';
import publicWidget from 'web.public.widget';

publicWidget.registry.payloxPlanResult = publicWidget.Widget.extend({
    selector: '.payment-plan-result #wrapwrap',

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            setTimeout(() => {
            const redirect = document.getElementById('redirect');
                if (redirect) {
                    if (redirect.value) {
                        window.location.href = redirect.value;
                    } else {
                        window.parent.document.querySelector('.o_form_payment_plan_pay').closest('.modal-content').querySelector('header button.close').click();
                    }
                }
            }, 2000);
        });
    },
});

export default publicWidget.registry.payloxTokenVerify;