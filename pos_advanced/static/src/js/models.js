odoo.define('pos_advanced.models', function (require) {
'use strict';

const PosModel = require('point_of_sale.models');

PosModel.load_fields('res.partner', ['type', 'child_ids', 'comment']);

const Order = PosModel.Order.prototype;
PosModel.Order = PosModel.Order.extend({
    initialize: function() {
        Order.initialize.apply(this, arguments);
        this.address = {};
    },

    init_from_JSON: function (json) {
        Order.init_from_JSON.apply(this, arguments);
        this.address = json.address;
    },

    export_as_JSON: function () {
        var res = Order.export_as_JSON.apply(this, arguments);
        res.address = this.address;
        return res;
    },

    get_address: function() {
        return this.get('address');
    },

    set_address: function(address) {
        this.assert_editable();
        this.set('address', address);
    },

    set_client: function(client) {
        Order.set_client.apply(this, arguments);
        this.set_address(client);
    },

});
});