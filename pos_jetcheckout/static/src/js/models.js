odoo.define('pos_jetcheckout.models', function (require) {
'use strict';

const PosModel = require('point_of_sale.models');
var PaymentJetcheckout = require('pos_jetcheckout.payment');

PosModel.register_payment_method('jetcheckout_virtual', PaymentJetcheckout);
PosModel.register_payment_method('jetcheckout_physical', PaymentJetcheckout);
PosModel.register_payment_method('jetcheckout_link', PaymentJetcheckout);
//PosModel.load_fields('pos.payment.method', 'jetcheckout_test');

const PosModelSuper = PosModel.PosModel.prototype;
PosModel.PosModel = PosModel.PosModel.extend({
    initialize: function() {
        PosModelSuper.initialize.apply(this, arguments);
        this.jetcheckout = {
            acquirer: 0,
            card: {
                type: [],
                family: [],
            }
        }

        this.models.push({
            label: 'payment.acquirer',
            loaded: function (self) {
                return self.session.rpc('/payment/card/acquirer', {}).then(function (acquirer) {
                    self.jetcheckout.acquirer = acquirer;
                });
            }
        }, {
            label: 'payment.card.type',
            loaded: function (self) {
                return self.session.rpc('/payment/card/type', {acquirer: self.jetcheckout.acquirer.id}).then(function (types) {
                    self.jetcheckout.card.type = types;
                });
            }
        }, {
            label: 'payment.card.family',
            loaded: function (self) {
                return self.session.rpc('/payment/card/family', {acquirer: self.jetcheckout.acquirer.id}).then(function (families) {
                    self.jetcheckout.card.family = families;
                });
            }
        });
    }
});

const Paymentline = PosModel.Paymentline.prototype;
PosModel.Paymentline = PosModel.Paymentline.extend({
    initialize: function() {
        Paymentline.initialize.apply(this, arguments);
        this.interval = undefined;
        this.transaction = undefined;
        this.popup = undefined;
        this.duration = 0;
    },

    remove_transaction() {
        clearInterval(this.interval);
        this.transaction = undefined;
        this.duration = 0;
    },

    set_duration(duration) {
        if (duration === -1) {
            this.duration -= 1;
        } else {
            this.duration = duration;
        }
        this.trigger('change', this);
    },

    close_popup() {
        if (this.popup) {
            this.popup.trigger('close-popup');
        }
    }
});

const Order = PosModel.Order.prototype;
PosModel.Order = PosModel.Order.extend({
    initialize: function() {
        Order.initialize.apply(this, arguments);
        this.transaction_ids = [];
    },

    init_from_JSON: function (json) {
        Order.init_from_JSON.apply(this, arguments);
        this.transaction_ids = json.transaction_ids;
    },

    export_as_JSON: function () {
        var res = Order.export_as_JSON.apply(this, arguments);
        res.transaction_ids = this.transaction_ids;
        return res;
    },

    stop_electronic_payment: function () {
        var lines = this.get_paymentlines();
        var line = lines.find(function (line) {
            var status = line.get_payment_status();
            return status && !['done', 'reversed', 'reversing', 'pending', 'waiting', 'retry'].includes(status);
        });
        if (line) {
            line.set_payment_status('waitingCancel');
            line.payment_method.payment_terminal.send_payment_cancel(this, line.cid).finally(function () {
                line.set_payment_status('retry');
            });
        }
    },
});
});