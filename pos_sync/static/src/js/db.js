odoo.define('pos_sync.DB', function (require) {
'use strict';

const PosDB = require('point_of_sale.DB');

PosDB.include({
    get_unpaid_orders: function() {
        var orders = this._super.apply(this, arguments);
        return orders.filter(order => order.is_owner);
    },
});
});