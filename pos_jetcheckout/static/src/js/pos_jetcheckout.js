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
        return this._jetcheckout_cancel(order, cid);
    },

    close: function () {
        this._super.apply(this, arguments);
    },

    _jetcheckout_pay: async function (cid) {
        const order = this.pos.get_order();
        const line = order.paymentlines.find(line => line.cid === cid);

        const amount = line.amount;
        if (amount <= 0) {
            Gui.showPopup('ErrorPopup', {
                title: _t('Error'),
                body: _t('Amount cannot be lower than zero'),
            });
            return;
        };

        const residual = order.get_due();
        if (amount > residual) {
            Gui.showPopup('ErrorPopup', {
                title: _t('Error'),
                body: _t('Amount cannot be higher than residual amount'),
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
            line.set_payment_status('waitingCard');
            await Gui.showPopup('JetcheckoutCardPopup', {
                order: order,
                line: line,
                amount: amount,
                partner: partner,
            });
        } else if (line.payment_method.use_payment_terminal === 'jetcheckout_link') {
            const duration = this.pos.config.jetcheckout_link_duration;
            if (!line.transaction) {
                line.set_payment_status('waiting');
                this._jetcheckout_set_interval(order, line, duration);
            }
            await Gui.showPopup('JetcheckoutLinkPopup', {
                order: order,
                line: line,
                amount: amount,
                partner: partner,
                duration: duration,
            });
        }
    },

    _jetcheckout_set_interval: function (order, line, duration) {
        line.remove_transaction();
        line.set_duration(duration);
        line.interval = setInterval(function() {
            if (line.duration === 0) {
                const transactionId = line.transaction && line.transaction.id || false;
                line.close_popup();
                line.remove_transaction();
                line.set_payment_status('timeout');
                if (transactionId) {
                    rpc.query({
                        route: '/pos/link/expire',
                        params: {id: transactionId}
                    }).then(function () {
                        return;
                    }).catch(function(error) {
                        console.error(error);
                        return;
                    });
                } else {
                    return;
                }
            }

            if (line.transaction && line.duration % 5 === 0) {
                rpc.query({
                    route: '/pos/link/query',
                    params: {id: line.transaction.id}
                }, {timeout: 1000}).then(function (result) {
                    if (result.status === 0) {
                        line.close_popup();
                        line.remove_transaction();
                        line.set_payment_status('done');
                        order.transaction_ids.push(result.id);
                        return;
                    } else if (result.status === -1) {
                        line.remove_transaction();
                        line.set_payment_status('retry');
                        Gui.showPopup('ErrorPopup', {
                            title: _t('Error'),
                            body: result.message || _t('An error occured. Please try again.'),
                        });
                        return;
                    }
                }).catch(function(error) {
                    console.error(error);
                });
            }
            line.set_duration(-1);
            try {
                line.popup.state.duration = line.duration;
            } catch {
                return;
            }
        }, 1000);
    },

    _jetcheckout_cancel: function (order, cid) {
        const line = order.paymentlines.find(line => line.cid === cid);
        if (line) {
            line.set_payment_status('retry');
            if (line.transaction) {
                return rpc.query({
                    route: '/pos/link/cancel',
                    params: {id: line.transaction.id}
                }).then(function () {
                    line.remove_transaction();
                    return Promise.resolve(true);
                }).catch(function(error) {
                    line.remove_transaction();
                    console.error(error);
                    return Promise.resolve(true);
                });
            } else {
                line.remove_transaction();
                return Promise.resolve(true);
            }
        }
        return Promise.resolve(true);
    },
});

return PaymentJetcheckout;
});
