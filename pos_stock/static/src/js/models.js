odoo.define('pos_stock.models', function (require) {
'use strict';

const exports = require('point_of_sale.models');
const field_utils = require('web.field_utils');
const { Gui } = require('point_of_sale.Gui');
const core = require('web.core');
const _t = core._t;

exports.load_fields('product.product', ['type']);

exports.load_models({
    model: 'stock.quant',
    fields: ['id', 'product_id', 'location_id', 'company_id', 'quantity', 'reserved_quantity'],
    domain: function (self) {
        return [['location_id.usage', 'in', ['internal']]];
    },
    loaded: function (self, quants) {
        self.db.add_quant(quants, self.config.picking_type);
    },
});

exports.load_models({
    model: 'stock.warehouse',
    fields: ['id', 'lot_stock_id', 'code', 'name'],
    loaded: function (self, warehouses) {
        self.db.add_warehouse(warehouses);
    },
});

exports.load_models({
    model: 'stock.location',
    fields: ['id', 'name', 'display_name', 'location_id'],
    loaded: function (self, locations) {
        self.db.add_location(locations);
    },
});

const PosModel = exports.PosModel.prototype;
exports.PosModel = exports.PosModel.extend({
    initialize: function () {
        this.is_ticket_screen_show = false;
        PosModel.initialize.call(this, ...arguments);
    },

    _after_flush_orders: function(orders) {
        console.log(orders);
        PosModel._after_flush_orders.call(this, ...arguments);
    },
});

const Order = exports.Order.prototype;
exports.Order = exports.Order.extend({
    destroy: function(){
        this.orderlines.remove(this.orderlines.models);
        Order.destroy.apply(this, arguments);
    },

    add_product: async function (product, options) {
        const self = this;
        const negativeOk = this.pos.config.picking_negative_ok;

        if (product.type !== 'product' || this._isRefundAndSaleOrder()) {
            return Order.add_product.apply(this, [product, options]);
        } else if (product.type === 'product' && !self.is_available(product) && !negativeOk) {
            await Gui.showPopup('ErrorPopup', {
                title: _t('Error'),
                body: _t('Quantity is not available'),
                silent: true,
            });
            return;
        }

        const quant = this.pos.db.quant_by_product_id[product.id];
        const warehouseId = this.pos.config.warehouse_id[0];
        let total = 0;
        var lot;
        var warehouse;
        var warehouses = [];
        var warehouseIds = [];

        if (quant) {
            if (negativeOk) {
                _.each(self.pos.config.warehouse_ids, function (id) {
                    warehouse = self.pos.db.warehouse_data_by_id[id];
                    lot = warehouse.lot_stock_id[0];
                    if (!quant[lot]) {
                        quant[lot] = 0;
                    }
                });
            }

            $.each(quant, function (key, value) {
                warehouse = self.pos.db.warehouse_by_id[key];
                lot = warehouse.lot_stock_id[0];
                if (warehouse) {
                    if (self.pos.config.warehouse_ids.includes(warehouse.id)) {
                        total += value;
                        warehouses.push({
                            id: warehouse.id,
                            name: warehouse.name,
                            lot: lot,
                            value: value,
                            default: warehouseId === warehouse.id,
                        });
                        warehouseIds.push(warehouse.id)
                    }
                }
            });
        } else {
            if (negativeOk) {
                _.each(self.pos.config.warehouse_ids, function (id) {
                    warehouse = self.pos.db.warehouse_data_by_id[id];
                    lot = warehouse.lot_stock_id[0];
                    warehouses.push({
                        id: warehouse.id,
                        name: warehouse.name,
                        lot: lot,
                        value: 0,
                        default: warehouseId === warehouse.id,
                    });
                });
            }
        }

        warehouses = warehouses.sort((x, y) => x.default > y.default ? -1 : 0)
        const { confirmed, payload } = await Gui.showPopup('StockPopup', {
            title: product.display_name,
            product: product.id,
            default: warehouseId,
            warehouses: warehouses,
            total: total
        });

        if (confirmed) {
            _.each(payload, async function (value) {
                await Order.add_product.apply(self, [product, {
                    quantity: field_utils.parse.float(value.quantity),
                    location_id: value.location_id,
                    transfer_type: value.transfer_type,
                    transfer_location: value.transfer_location,
                    transfer_date: value.transfer_date,
                    merge: false,
                }]);
            });
        }
    },

    set_orderline_options: function (orderline, options) {
        if (options.transfer_date !== undefined) {
            orderline.set_transfer_date(options.transfer_date);
        }
        if (options.transfer_type !== undefined) {
            orderline.set_transfer_type(options.transfer_type);
        }
        if (options.transfer_location !== undefined) {
            orderline.set_transfer_location(options.transfer_location);
        }
        if (options.location_id !== undefined) {
            orderline.set_location(options.location_id);
            orderline.quantity = 0;
        }
        Order.set_orderline_options.apply(this, [orderline, options]);
    },

    is_available: function (product) {
        const self = this;
        const quant = this.pos.db.quant_by_product_id[product.id];
        let is_available = false;

        if (quant) {
            $.each(quant, function (key, value) {
                var warehouse = self.pos.db.warehouse_by_id[key];
                if (warehouse && self.pos.config.warehouse_ids.includes(warehouse.id)) {
                    is_available = self.pos.config.picking_negative_ok || value > 0;
                    return false;
                }
            });
        }
        return is_available;
    }
});

const Orderline = exports.Orderline.prototype;
exports.Orderline = exports.Orderline.extend({
    initialize: function () {
        this.location_id = false;
        this.transfer_type = false;
        this.transfer_location = false;
        this.transfer_date = false;
        Orderline.initialize.call(this, ...arguments);
        this.on('remove', this.on_remove, this);
    },

    on_remove: function () {
        try {
            this.set_quantity(0);
        } catch {}
    },

    set_location: function (location_id) {
        this.location_id = location_id || false;
    },

    get_location: function () {
        return this.location_id || false;
    },

    set_transfer_type: function (transfer_type) {
        this.transfer_type = transfer_type || false;
    },

    get_transfer_type: function () {
        return this.transfer_type || false;
    },

    set_transfer_location: function (transfer_location) {
        this.transfer_location = transfer_location || false;;
    },

    get_transfer_location: function () {
        return this.transfer_location || false;
    },

    set_transfer_date: function (transfer_date) {
        this.transfer_date = transfer_date || false;
    },

    get_transfer_date: function () {
        return this.transfer_date && new Date(this.transfer_date).toLocaleDateString() || '';
    },

    set_quantity: function (quantity, keep_price) {
        if (this.location_id && quantity !== 'remove') {
            const quant = this.pos.db.quant_by_product_id[this.product.id];
            const qty = quant[this.location_id] + (this.quantity || 0) - (field_utils.parse.float('' + quantity) || 0);
            const $qty = $('div.product-list article[data-product-id=' + this.product.id + '] span.quantity-available');

            if (qty <= 0) {
                $qty.addClass('absent');
                if (qty < 0) {
                    Gui.showPopup('ErrorPopup', {
                        title: _t('Error'),
                        body: _t('Quantity is not available'),
                        silent: true,
                    });
                    return;
                }
            } else {
                $qty.removeClass('absent');
            }

            $qty.text(qty);
            quant[this.location_id] = qty;
        }
        return Orderline.set_quantity.call(this, quantity, keep_price);
    },

    export_for_printing: function () {
        const lines = Orderline.export_for_printing.call(this);
        $.extend(lines, { location_id: this.get_location() || false });
        return lines;
    },

    export_as_JSON: function () {
        const json = Orderline.export_as_JSON.call(this);
        json.location_id = this.location_id;
        json.transfer_type = this.transfer_type;
        json.transfer_date = this.transfer_date;
        json.transfer_location = this.transfer_location;
        return json;
    },

    init_from_JSON: function (json) {
        this.set_location(json.location_id);
        this.set_transfer_date(json.transfer_date);
        this.set_transfer_type(json.transfer_type);
        this.set_transfer_location(json.transfer_location);
        Orderline.init_from_JSON.apply(this, arguments);
    },
});
});
