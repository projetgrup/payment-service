odoo.define('pos_stock.models', function (require) {
'use strict';

const exports = require('point_of_sale.models');
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
        self.db.add_quant(quants);
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
    initialize: function (session, attributes) {
        this.is_ticket_screen_show = false;
        PosModel.initialize.call(this, session, attributes);
    }
});

const Order = exports.PosModel.prototype;
exports.Order = exports.Order.extend({
    add_product: async function (product, options) {
        const self = this;

        if (product.type !== 'product' || this._isRefundAndSaleOrder()) {
            return Order.add_product.apply(this, [product, options]);
        }

        if (product.type === 'product' && self.get_warehouse(product.id).length == 0 && !self.pos.config.picking_negative_ok) {
            await this.showPopup('ErrorPopup', {
                title: _t('Error'),
                body: _t('Quantity is not available'),
            });
        } else {
            if (product.type === 'product' && !product.added) {
                var product_id = product.id;
                var warehouse_id = this.pos.config.warehouse_id[0];
                var quant_by_product_id = this.pos.db.quant_by_product_id[product_id];
                var total_qty = 0;
                var product_warehouse;
                var warehouses = [];
                var warehouse_ids = [];

                if (quant_by_product_id) {
                    var warehouse_list = [];
                    if (self.pos.config.picking_negative_ok) {
                        _.each(self.pos.config.warehouse_ids, function (id) {
                            if (warehouse_list.indexOf(id) == (-1)) {
                                var warehouse = self.pos.db.warehouse_data_by_id[id];
                                if (self.pos.db.quant_by_product_id[product_id] && !self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id[0]]) {

                                    self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id[0]] = {};
                                    if (self.pos.config.picking_type == 'quantity_available') {
                                        self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id[0]] = {'quantity_available': 0}
                                    }
                                    if (self.pos.config.picking_type == 'quantity_unreserved') {
                                        self.pos.db.quant_by_product_id[product_id][warehouse.lot_stock_id[0]] = {'quantity_unreserved': 0}
                                    }
                                }
                            }
                        });
                    }

                    $.each(quant_by_product_id, function (key, value) {
                        var warehouse = self.pos.db.warehouse_by_id[key];
                        product_warehouse = warehouse;
                        if (warehouse) {
                            if (self.pos.config.warehouse_ids.includes(warehouse.id)) {
                                if (self.pos.config.picking_type == "quantity_available") {
                                    total_qty += parseInt(value["quantity_available"]);
                                    warehouses.push({
                                        default: warehouse_id === warehouse.id,
                                        lot_stock_id: warehouse.lot_stock_id[0],
                                        warehouse_name: warehouse["name"],
                                        value: value["quantity_available"],
                                        warehouse_id: warehouse.id
                                    });
                                    warehouse_ids.push(warehouse.id)
                                }
                                if (self.pos.config.picking_type == "quantity_unreserved") {
                                    total_qty += parseInt(value["quantity_unreserved"]);
                                    warehouses.push({
                                        default: warehouse_id === warehouse.id,
                                        lot_stock_id: warehouse.lot_stock_id[0],
                                        warehouse_name: warehouse["name"],
                                        value: value["quantity_unreserved"],
                                        warehouse_id: warehouse.id
                                    });
                                    warehouse_ids.push(warehouse.id)
                                }
                            }
                        }
                    });

                } else {
                    if (self.pos.config.picking_negative_ok) {
                        _.each(self.pos.config.warehouse_ids, function (id) {
                            var warehouse = self.pos.db.warehouse_data_by_id[id];
                            warehouses.push({
                                default: warehouse_id === warehouse.id,
                                lot_stock_id: warehouse.lot_stock_id[0],
                                warehouse_name: warehouse["name"],
                                value: 0,
                                warehouse_id: warehouse.id
                            });
                        });
                    }
                }
                var product_warehouse_data_total = {total: total_qty};
                warehouses = warehouses.sort((x, y) => x.default > y.default ? -1 : 0)
                Gui.showPopup("StockPopup", {
                    title: product.display_name,
                    product: product.id,
                    warehouse: warehouse_id,
                    warehouses: warehouses,
                    product_warehouse_data_total: product_warehouse_data_total
                });
            } else {
                if (this.pos.doNotAllowRefundAndSales() && this._isRefundAndSaleOrder()) {
                    await Gui.showPopup('ErrorPopup', {
                        'title': _t("POS error"),
                        'body': _t("Can't mix order with refund products with new products."),
                    });
                    return false;
                }

                product.added = false;
                if (this._printed) {
                    this.destroy();
                    return this.pos.get_order().add_product(product, options);
                }
                this.assert_editable();
                options = options || {};
                var attr = JSON.parse(JSON.stringify(product));
                attr.pos = this.pos;
                attr.order = this;
                var line = new models.Orderline({}, {pos: this.pos, order: this, product: product});

                this.set_orderline_options(line, options);

                var to_merge_orderline;

                for (var i = 0; i < this.orderlines.length; i++) {
                    if (this.orderlines.at(i).can_be_merged_with(line) && options.merge !== false) {
                        to_merge_orderline = this.orderlines.at(i);
                    }
                }
                if (to_merge_orderline) {
                    to_merge_orderline.merge(line);
                    this.select_orderline(to_merge_orderline);
                } else {
                    this.orderlines.add(line);
                    this.select_orderline(this.get_last_orderline());
                }

                if (line.has_product_lot) {
                    this.display_lot_popup();
                }
                if (this.pos.config.iface_customer_facing_display) {
                    this.pos.send_current_order_to_customer_facing_display();
                }
                this.trigger('update-rewards');
            }
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
        }
        Order.set_orderline_options.apply(this, [orderline, options]);
    },

    get_warehouse: function (product_id) {
        var self = this;
        var quant_by_product_id = this.pos.db.quant_by_product_id[product_id];
        var product_warehouse = [];

        if (quant_by_product_id) {
            $.each(quant_by_product_id, function (key, value) {
                var warehouse = self.pos.db.warehouse_by_id[key];
                if (warehouse) {
                    if (self.pos.config.warehouse_ids.includes(warehouse.id)) {
                        if (!self.pos.config.picking_negative_ok) {
                            if (self.pos.config.picking_type == "quantity_available" && value.quantity_available >= 0) {
                                product_warehouse.push(warehouse);
                            }
                            if (self.pos.config.picking_type == "quantity_unreserved" && value.quantity_unreserved >= 0) {
                                product_warehouse.push(warehouse);
                            }
                        } else {
                            product_warehouse.push(warehouse);
                        }
                    }
                }
            });
        }
        return product_warehouse;
    }
});

const Orderline = exports.PosModel.prototype;
exports.Orderline = models.Orderline.extend({
    initialize: function (attr, options) {
        this.location_id = this.location_id || false;
        this.transfer_date = this.transfer_date || false;
        this.transfer_type = this.transfer_type || false;
        this.transfer_location = this.transfer_location || false;
        Orderline.initialize.call(this, attr, options);
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

    set_quantity: function (quantity, keep_price) {
        const self = this;
        try {
            if (!this.order.is_owner()) {
                return Orderline.set_quantity.call(this, quantity, keep_price);
            }
        } catch {}

        const currentOrder = this.env.pos.get_order();

        if (self.quantity && (quantity || quantity == 0) && self.product && self.product.id && self.location_id && self.pos.db.quant_by_product_id && self.pos.db.quant_by_product_id[self.product.id] && ((self.pos.db.quant_by_product_id[self.product.id][self.location_id]) || (self.pos.db.quant_by_product_id[self.product.id][self.location_id] == 0)) && currentOrder && !currentOrder.temp && !self.pos.config.picking_negative_ok) {
            if (self.pos.config.picking_type == 'quantity_available') {
                self.pos.db.quant_by_product_id[self.product.id][self.location_id]['quantity_available'] = self.pos.db.quant_by_product_id[self.product.id][self.location_id]['quantity_available'] + self.quantity
            } else if (self.pos.config.picking_type == 'quantity_unreserved') {
                self.pos.db.quant_by_product_id[self.product.id][self.location_id]['quantity_unreserved'] = self.pos.db.quant_by_product_id[self.product.id][self.location_id]['quantity_unreserved'] + self.quantity
            }
        }

        if (self.pos.config.warehouse_ids && self.pos.config.warehouse_ids.length > 0 && this.product.type == "product") {
            if (self.pos.config.picking_negative_ok) {
                var product_id = this.product.id
                if (product_id) {
                    var quant_by_product_id = self.pos.db.quant_by_product_id[product_id];
                    if (quant_by_product_id) {

                        if (self.location_id && quant_by_product_id[self.location_id]) {
                            if (self.pos.config.picking_type) {
                                var class1 = $('article[data-product-id=' + self.product.id + ']').find('.quantity_available')
                                if (self.pos.config.picking_type == 'quantity_available') {
                                    self.product['sh_pos_stock'] = self.product['sh_pos_stock_temp'] - quantity
                                    var total_stock = 0

                                    if (class1.length > 0) {
                                        total_stock = parseFloat(class1.text())
                                    }

                                    if (currentOrder&& currentOrder.temp) {
                                        total_stock = total_stock - quantity
                                        quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] - quantity
                                    } else {

                                        if (!quantity) {
                                            total_stock = total_stock + this.quantity
                                            quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] + this.quantity
                                        } else {

                                            if (this.quantity - quantity > 0) {
                                                total_stock = total_stock + (this.quantity - quantity) - 1
                                                quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] + total_stock
                                            } else if (this.quantity - quantity < 0) {
                                                total_stock = total_stock - (quantity - this.quantity)
                                                quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] - (quantity - this.quantity)
                                            }
                                        }
                                    }
                                    if (class1.length > 0) {
                                        class1.text(parseFloat(total_stock))
                                    }
                                    _super_orderline.set_quantity.call(this, quantity, keep_price);

                                } else if (self.pos.config.picking_type == 'quantity_unreserved') {
                                    self.product['sh_pos_stock'] = self.product['sh_pos_stock_temp'] - quantity
                                    var total_stock = 0

                                    if (class1.length > 0) {
                                        total_stock = parseFloat(class1.text())
                                    }

                                    if (currentOrder&& currentOrder.temp) {
                                        total_stock = total_stock - quantity
                                        quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] - quantity
                                    } else {

                                        if (!quantity) {
                                            total_stock = total_stock + this.quantity
                                            quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] + this.quantity
                                        } else {

                                            if (this.quantity - quantity > 0) {
                                                total_stock = total_stock + (this.quantity - quantity) - 1
                                                quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] + total_stock
                                            } else if (this.quantity - quantity < 0) {
                                                total_stock = total_stock - (quantity - this.quantity)
                                                quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] - (quantity - this.quantity)
                                            }
                                        }
                                    }
                                    if (class1.length > 0) {
                                        class1.text(parseFloat(total_stock))
                                    }
                                    _super_orderline.set_quantity.call(this, quantity, keep_price);
                                }
                            }
                        } else {
                            _super_orderline.set_quantity.call(this, quantity, keep_price);
                        }
                    }
                }
                return _super_orderline.set_quantity.call(this, quantity, keep_price);
            } else {
                var product_id = this.product.id

                if (product_id) {
                    var quant_by_product_id = self.pos.db.quant_by_product_id[product_id];

                    if (quant_by_product_id) {
                        if (self.location_id && quant_by_product_id[self.location_id]) {
                            if (self.pos.config.picking_type) {
                                if (self.pos.config.picking_type == 'quantity_available') {
                                    if (quant_by_product_id[self.location_id]['quantity_available']) {

                                        if (quantity == "remove") {
                                            _super_orderline.set_quantity.call(this, quantity, keep_price);
                                        } else {
                                            var class1 = $('article[data-product-id=' + self.product.id + ']').find('.quantity_available')

                                            if (quantity <= quant_by_product_id[self.location_id]['quantity_available']) {

                                                self.product['sh_pos_stock'] = self.product['sh_pos_stock_temp'] - quantity
                                                var total_stock = 0

                                                if (class1.length > 0) {
                                                    total_stock = parseFloat(class1.text())
                                                }

                                                if (currentOrder&& currentOrder.temp) {
                                                    total_stock = total_stock - quantity
                                                    quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] - quantity
                                                } else {

                                                    if (!quantity) {
                                                        total_stock = total_stock + this.quantity
                                                    } else {

                                                        if (this.quantity - quantity > 0) {
                                                            // total qty -2 bcz of if negative salling is off then orderline qty will added in startig of method
                                                            total_stock = total_stock + (this.quantity - quantity) - 2
                                                            quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] + total_stock
                                                        } else if (this.quantity - quantity < 0) {
                                                            total_stock = total_stock - (quantity - this.quantity)
                                                            quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] - (quantity - this.quantity)
                                                        }
                                                    }
                                                }

                                                if (class1.length > 0) {
                                                    class1.text(parseFloat(total_stock))
                                                }

                                                return _super_orderline.set_quantity.call(this, quantity, keep_price);
                                            } else {
                                                quant_by_product_id[self.location_id]['quantity_available'] = quant_by_product_id[self.location_id]['quantity_available'] - self.quantity

                                                if (!self.pos.is_ticket_screen_show) {
                                                    alert("Sufficient Quantity Not Available")
                                                }

                                                if (quantity == 'remove') {
                                                    return _super_orderline.set_quantity.call(this, quantity, keep_price);
                                                }
                                            }
                                        }
                                    } else {

                                        if (!self.pos.is_ticket_screen_show) {
                                            alert("Sufficient Quantity Not Available")
                                        }
                                    }
                                } else if (self.pos.config.picking_type == 'quantity_unreserved') {

                                    if (quant_by_product_id[self.location_id]['quantity_unreserved']) {

                                        if (quantity == "remove") {
                                            _super_orderline.set_quantity.call(this, quantity, keep_price);
                                        } else {
                                            var class1 = $('article[data-product-id=' + self.product.id + ']').find('.quantity_available')

                                            if (quantity <= quant_by_product_id[self.location_id]['quantity_unreserved']) {
                                                self.product['sh_pos_stock'] = self.product['sh_pos_stock_temp'] - quantity
                                                var total_stock = 0

                                                if (class1.length > 0) {
                                                    total_stock = parseFloat(class1.text())
                                                }

                                                if (currentOrder&& currentOrder.temp) {
                                                    total_stock = total_stock - quantity
                                                    quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] - quantity
                                                } else {
                                                    if (!quantity) {
                                                        total_stock = total_stock + this.quantity

                                                        // quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] + this.quantity
                                                    } else {
                                                        quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] - quantity
                                                        total_stock = total_stock + (this.quantity - quantity)
                                                    }
                                                }

                                                if (class1.length > 0) {
                                                    class1.text(parseFloat(total_stock))
                                                }

                                                return Orderline.set_quantity.call(this, quantity, keep_price);
                                            } else {
                                                quant_by_product_id[self.location_id]['quantity_unreserved'] = quant_by_product_id[self.location_id]['quantity_unreserved'] - self.quantity

                                                if (!self.pos.is_ticket_screen_show) {
                                                    alert("Sufficient Quantity Not Available")
                                                }

                                                if (quantity == 'remove') {
                                                    return Orderline.set_quantity.call(this, quantity, keep_price);
                                                }
                                            }
                                        }
                                    } else {
                                        if (!self.pos.is_ticket_screen_show) {
                                            alert("Sufficient Quantity Not Available")
                                        }
                                    }
                                }
                            }
                        } else {
                            return Orderline.set_quantity.call(this, quantity, keep_price);
                        }
                    }
                }
            }
        } else {
            return Orderline.set_quantity.call(this, quantity, keep_price);
        }

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
        if (json) {
            this.set_location(json.location_id);
            this.set_transfer_date(json.transfer_date);
            this.set_transfer_type(json.transfer_type);
            this.set_transfer_location(json.transfer_location);
        }
        Orderline.init_from_JSON.apply(this, arguments);
    },
});
});
