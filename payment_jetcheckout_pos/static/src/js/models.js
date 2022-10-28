odoo.define('payment_jetcheckout_pos.models', function (require) {
'use strict';

const PosModel = require('point_of_sale.models');

const PosModelSuper = PosModel.PosModel.prototype;
PosModel.PosModel = PosModel.PosModel.extend({
    initialize: function() {
        PosModelSuper.initialize.apply(this, arguments);
        this.models.push({
            label: 'payment.acquirer',
            loaded: function (self) {
                return self.session.rpc('/payment/card/acquirer',{}).then(function (acquirer) {
                    self.vpos_acquirer = acquirer;
                    self.vpos_card_types = [];
                    self.vpos_card_families = [];
                });
            }
        }, {
            label: 'payment.card.type',
            loaded: function (self) {
                return self.session.rpc('/payment/card/type', {acquirer: self.vpos_acquirer.id}).then(function (types) {
                    self.vpos_card_types = types;
                });
            }
        }, {
            label: 'payment.card.family',
            loaded: function (self) {
                return self.session.rpc('/payment/card/family', {acquirer: self.vpos_acquirer.id}).then(function (families) {
                    self.vpos_card_families = families;
                });
            }
        });
        /*const method = _.find(this.models, function(model){
            return model.model === 'pos.payment.method';
        });
        if (method) {
            method.fields.push('');
        }*/
    }
});
});