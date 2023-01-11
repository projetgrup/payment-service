odoo.define('pos_jetcheckout.models', function (require) {
'use strict';

const PosModel = require('point_of_sale.models');
var PaymentJetcheckout = require('pos_jetcheckout.payment');

PosModel.register_payment_method('jetcheckout_virtual', PaymentJetcheckout);
PosModel.register_payment_method('jetcheckout_physical', PaymentJetcheckout);
PosModel.register_payment_method('jetcheckout_link', PaymentJetcheckout);
PosModel.load_fields('pos.payment.method', 'jetcheckout_link_url');
PosModel.load_fields('pos.payment.method', 'jetcheckout_link_apikey');
PosModel.load_fields('pos.payment.method', 'jetcheckout_link_secretkey');

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

const Order = PosModel.Order.prototype;
PosModel.Order = PosModel.Order.extend({
    initialize: function() {
        Order.initialize.apply(this, arguments);
        this.transaction_id = 0;
        this.transaction_ids = [];
    },

    init_from_JSON: function (json) {
        Order.init_from_JSON.apply(this, arguments);
        this.transaction_id = json.transaction_id;
        this.transaction_ids = json.transaction_ids;
    },

    export_as_JSON: function () {
        var res = Order.export_as_JSON.apply(this, arguments);
        res.transaction_id = this.transaction_id;
        res.transaction_ids = this.transaction_ids;
        return res;
    },
});
});