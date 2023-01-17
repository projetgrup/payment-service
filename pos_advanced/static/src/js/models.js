odoo.define('pos_advanced.models', function (require) {
'use strict';

const PosModel = require('point_of_sale.models');

PosModel.register_payment_method('payment_bank', PaymentBank);
//PosModel.load_fields('pos.payment.method', 'test');


});