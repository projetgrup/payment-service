odoo.define('payment_jetcheckout.payment_form', require => {
    'use strict';

    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');

    const paymentJetcheckout = {
        _processPayment: function (provider, paymentOptionId, flow) {
            if (provider !== 'jetcheckout') {
                return this._super(...arguments);
            }
            $('#payment_pay').trigger('click');
            return Promise.resolve();
        },
    };
    checkoutForm.include(paymentJetcheckout);
    manageForm.include(paymentJetcheckout);
});