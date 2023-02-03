odoo.define('pos_advanced.models', function (require) {
'use strict';

const PosModel = require('point_of_sale.models');

PosModel.load_fields('res.partner', ['type', 'child_ids', 'comment', 'debit', 'credit']);

PosModel.PosModel = PosModel.PosModel.extend({
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

const Order = PosModel.Order.prototype;
PosModel.Order = PosModel.Order.extend({
    initialize: function() {
        this.partner_address = { id: null, delivery: null, invoice: null };
        this.set({ address: this.partner_address });
        Order.initialize.apply(this, arguments);
    },

    init_from_JSON: function (json) {
        Order.init_from_JSON.apply(this, arguments);
        this.partner_address = json.partner_address;
        this.set({ address: this.partner_address });
    },

    export_as_JSON: function () {
        var res = Order.export_as_JSON.apply(this, arguments);
        res.partner_address = this.get_address();
        return res;
    },

    get_address: function() {
        return this.get('address') || this.partner_address;
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