odoo.define('pos_advanced.models', function (require) {
'use strict';

const exports = require('point_of_sale.models');

exports.load_fields('res.partner', ['type', 'child_ids', 'comment', 'debit', 'credit']);
exports.load_fields('pos.payment.method', ['icon']);

const PosModel = exports.PosModel.prototype;
exports.PosModel = exports.PosModel.extend({
    initialize: function() {
        PosModel.initialize.apply(this, arguments);
        var self = this;
        this.set({'selectedAddress': this.get_address()});

        function update_address() {
            this.set('selectedAddress', self.get_address());
        }

        this.get('orders').on('add remove change', update_address, this);
        this.on('change:selectedAddress', update_address, this);
    },

    get_address: function() {
        var order = this.get_order();
        if (order) {
            return order.get_address();
        }
        return { id: null, delivery: null, invoice: null };
    },

    get_country_code: function(cid) {
        const country = this.env.pos.countries.find(c => c.id === cid);
        return country && country.code || '';
    },
});

const Order = exports.Order.prototype;
exports.Order = exports.Order.extend({
    initialize: function() {
        this.partner_address = { id: null, delivery: null, invoice: null };
        this.set({ address: this.partner_address });
        Order.initialize.apply(this, arguments);
    },

    init_from_JSON: function (json) {
        Order.init_from_JSON.apply(this, arguments);
        this.partner_address = json.partner_address;
        const address = { id: null, delivery: null, invoice: null }
        if (this.partner_address) {
            address.id = this.partner_address.id || null;
            address.delivery = this.partner_address.delivery ? this.pos.db.get_partner_by_id(this.partner_address.delivery) : null;
            address.invoice = this.partner_address.invoice ? this.pos.db.get_partner_by_id(this.partner_address.invoice) : null;
        }
        this.set({ address: address });
    },

    export_as_JSON: function () {
        var res = Order.export_as_JSON.apply(this, arguments);
        const address = this.get_address();
        if (address) {
            res.partner_address = { id: address.id || null, delivery: address.delivery && address.delivery.id || null, invoice: address.invoice && address.invoice.id || null };
        } else {
            res.partner_address = { id: null, delivery: null, invoice: null };
        }
        return res;
    },

    get_address: function() {
        return this.get('address') || { id: null, delivery: null, invoice: null };
    },

    set_address: function(address) {
        this.assert_editable();
        this.set('address', {...this.get('address'), ...address});
    },

    set_client: function(client) {
        Order.set_client.apply(this, arguments);
        if (client) {
            if (this.get_address().id !== client.id) {
                this.set_address({ id: client.id, delivery: client, invoice: client });
            }
        } else {
            this.set_address({ id: null, delivery: null, invoice: null });
        }
    },

});
});