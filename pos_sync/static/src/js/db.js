odoo.define('pos_sync.DB', function (require) {
'use strict';

const PosDB = require('point_of_sale.DB');

PosDB.include({
    get_unpaid_orders: function() {
        const orders = [];
        const unpaid_orders = this._super.apply(this, arguments);
        if (!unpaid_orders) {
            return unpaid_orders;
        }

        for (let i=0; i < unpaid_orders.length; i++) {
            if (unpaid_orders[i]) {
                if (unpaid_orders[i].is_owner) {
                    orders.push(unpaid_orders[i]);
                } else {
                    this.remove_unpaid_order(unpaid_orders[i]);
                }
            }
        }
        return orders;
    },

    save_unpaid_order: function(order) {
        if (!order.is_owner) {
            return order.uid;
        }
        return this._super.apply(this, arguments);
    },
});
});