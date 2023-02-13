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
        this.transfer_type_by_code = {
            'immediately': _('Immediately'),
            'later': _('Later'),
        };
        this.transfer_method_by_code = {
            'shopping': _('Shopping'),
            'cargo_paid': _('Paid Cargo'),
            'cargo_free': _('Free Cargo'),
            'vehicle': _('Vehicle'),
        };
        this.lot_stock_list = [];
        this.location_by_id = {};
        this.warehouse_data_by_id = {};
    },

    add_warehouse: function (warehouses) {
        for (let i=0; i < warehouses.length; i++) {
            var warehouse = warehouses[i];
            var lot = warehouse.lot_stock_id[0];
            this.warehouse_by_id[lot] = warehouse;
            this.lot_stock_list.push(lot);
            this.warehouse_data_by_id[warehouse.id] = warehouse;
        }
    },

    add_location: function (locations) {
        for (let i=0; i < locations.length; i++) {
            var location = locations[i];
            this.location_by_id[location.id] = location;
        }
    },

    add_quant: function (quants, type) {
        if (!quants instanceof Array) {
            quants = [quants];
        }

        const unreserved = type === 'quantity_unreserved';
        for (let i=0; i < quants.length; i++) {
            var quant = quants[i];
            this.quants.push(quant);
            this.quant_by_id[quant.id] = quant;

            var product_id = quant.product_id[0];
            var location_id = quant.location_id[0];

            if (!(product_id in this.quant_by_product_id)) {
                this.quant_by_product_id[product_id] = {};
            }

            if (!(location_id in this.quant_by_product_id[product_id])) {
                this.quant_by_product_id[product_id][location_id] = 0;
            }

            var quantity = quant.quantity;
            if (unreserved) {
                quantity -= quant.reserved_quantity;
            }

            this.quant_by_product_id[product_id][location_id] += quantity;
        }
    },
});
});
