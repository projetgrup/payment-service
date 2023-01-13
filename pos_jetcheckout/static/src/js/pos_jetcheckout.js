odoo.define('pos_jetcheckout.payment', function (require) {
"use strict";

const { Gui } = require('point_of_sale.Gui');
var rpc = require('web.rpc');
var core = require('web.core');
var PaymentInterface = require('point_of_sale.PaymentInterface');

var _t = core._t;

var PaymentJetcheckout = PaymentInterface.extend({
    send_payment_request: function (cid) {
        this._super.apply(this, arguments);
        return this._jetcheckout_pay(cid);
    },

    send_payment_cancel: function (order, cid) {
        this._super.apply(this, arguments);
        return this._jetcheckout_cancel();
    },

    close: function () {
        this._super.apply(this, arguments);
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
        if (!(partner > 0)) {
            Gui.showPopup('ErrorPopup', {
                title: _t('Error'),
                body: _t('Please select a customer'),
            });
            return;
        };

        if (line.payment_method.use_payment_terminal === 'jetcheckout_virtual') {
            await Gui.showPopup('JetcheckoutCardPopup', {
                order: order,
                line: line,
                amount: amount,
                partner: partner,
            });
        } else if (line.payment_method.use_payment_terminal === 'jetcheckout_link') {
            await Gui.showPopup('JetcheckoutLinkPopup', {
                order: order,
                line: line,
                amount: amount,
                partner: partner,
            });
        }
    },

    _jetcheckout_cancel: function () {
        const order = this.pos.get_order();
        if (order.transaction_id > 0) {
            return rpc.query({
                route: '/pos/link/cancel',
                params: {tx: order.transaction_id}
            }).then(function () {
                order.transaction_id = 0;
                return Promise.resolve(true);
            }).catch(function(error) {
                console.log(error);
                order.transaction_id = 0;
                return Promise.resolve(true);
            });
        } else {
            order.transaction_id = 0;
            return Promise.resolve(true);
        }
    },
});

return PaymentJetcheckout;
});
