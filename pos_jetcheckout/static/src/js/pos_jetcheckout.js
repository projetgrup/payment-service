odoo.define('pos_jetcheckout.payment', function (require) {
"use strict";

var core = require('web.core');
var PaymentInterface = require('point_of_sale.PaymentInterface');
const { Gui } = require('point_of_sale.Gui');

var _t = core._t;

var PaymentJetcheckout = PaymentInterface.extend({
    send_payment_request: function (cid) {
        this._super.apply(this, arguments);
        return this._jetcheckout_pay(cid);
    },

    send_payment_cancel: function (order, cid) {
        this._super.apply(this, arguments);
        return Promise.resolve(true);
    },

    close: function () {
        this._super.apply(this, arguments);
    },

    _pending_jetcheckout_virtual_line() {
      return this.pos.get_order().paymentlines.find(paymentLine => paymentLine.payment_method.use_payment_terminal === 'jetcheckout_virtual' && (!paymentLine.is_done()));
    },

    _jetcheckout_pay: async function (cid) {
        const order = this.pos.get_order();
        const line = order.paymentlines.find(line => line.cid === cid);
        line.set_payment_status('waitingCard');

        const amount = line.amount;
        if (amount <= 0) {
            Gui.showPopup('ErrorPopup', {
                title: _t('Error'),
                body: _t('Amount cannot be lower than zero'),
            });
            return;
        };

        const client = order.get_client();
        const partner = client && client.id || 0;

        await Gui.showPopup('CardPopup', {
            order: order,
            line: line,
            amount: amount,
            partner: partner,
        });
    },
});

return PaymentJetcheckout;
});
