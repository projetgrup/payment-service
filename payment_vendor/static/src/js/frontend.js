odoo.define('payment_vendor.payment_page', function (require) {
"use strict";

var publicWidget = require('web.public.widget');
var systemPage = publicWidget.registry.JetcheckoutPaymentSystemPage;

publicWidget.registry.VendorPaymentPage = systemPage.extend({
    selector: '.payment-vendor #wrapwrap',
});


});