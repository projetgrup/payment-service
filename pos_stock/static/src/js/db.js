odoo.define('pos_stock.db', function (require) {
'use strict';

var DB = require('point_of_sale.DB');

DB.include({
    init: function (options) {
        this._super(options);
        this.quants = [];
        this.quant_by_id = {};
        this.quant_by_product_id = {};
        this.picking_type_by_id = {};
        this.warehouse_by_id = {};
        this.lot_stock_list = [];
        this.location_by_id = {};
        this.warehouse_data_by_id = {};
    },

    add_warehouse: function (warehouses) {
        for (let i=0; i < warehouses.length; i++) {
            const warehouse = warehouses[i];
            this.warehouse_by_id[warehouse.lot_stock_id[0]] = warehouse;
            this.lot_stock_list.push(warehouse.lot_stock_id[0]);
            this.warehouse_data_by_id[warehouse.id] = warehouse;
        }
    },

    add_location: function (locations) {
        for (let i=0; i < locations.length; i++) {
            const location = locations[i];
            this.location_by_id[location.id] = location;
        }
    },

    add_quant: function (quants) {
        if (!quants instanceof Array) {
            quants = [quants];
        }

        for (let i=0; i < quants.length; i++) {
            var quant = quants[i];
            this.quants.push(quant);
            this.quant_by_id[quant.id] = quant;

            if (quant.product_id[0] in this.quant_by_product_id) {
                var location = this.quant_by_product_id[quant.product_id[0]];
                if (quant.location_id[0] in location) {
                    var quantity = location[quant.location_id[0]];
                    location[quant.location_id[0]] = {
                        quantity_available: quant.quantity + quantity,
                        quantity_unreserved: quant.quantity + quantity - quant.reserved_quantity
                    };
                } else {
                    location[quant.location_id[0]] = {
                        quantity_available: quant.quantity,
                        quantity_unreserved: quant.quantity - quant.reserved_quantity
                    };
                }
                this.quant_by_product_id[quant.product_id[0]] = location;
            } else {
                var location = {};
                location[quant.location_id[0]] = {
                    quantity_available: quant.quantity,
                    quantity_unreserved: quant.quantity - quant.reserved_quantity
                };
                this.quant_by_product_id[quant.product_id[0]] = location;
            }
        }
    },
});
});
