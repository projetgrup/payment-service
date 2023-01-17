odoo.define('pos_advanced.bank', function (require) {
"use strict";

var PaymentInterface = require('point_of_sale.PaymentInterface');
var PaymentBank = PaymentInterface.extend({});
return PaymentBank;
});
