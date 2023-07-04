/** @odoo-module alias=paylox.form **/
'use strict';

import checkoutForm from 'payment.checkout_form';
import manageForm from 'payment.manage_form';

const paymentPaylox = {
    _processPayment: function (provider, paymentOptionId, flow) {
        if (provider !== 'jetcheckout') {
            return this._super(...arguments);
        }
        $('[field="payment.button"]').trigger('click');
        return Promise.resolve();
    },
};

checkoutForm.include(paymentPaylox);
manageForm.include(paymentPaylox);