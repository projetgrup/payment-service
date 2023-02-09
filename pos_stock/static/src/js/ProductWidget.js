odoo.define('pos_stock.ProductWidget', function (require) {
'use strict';

const ProductsWidget = require('point_of_sale.ProductsWidget');
const Registries = require('point_of_sale.Registries');
const TicketScreen = require('point_of_sale.TicketScreen');
const RefundButton = require('point_of_sale.RefundButton');

const StockRefundButton = (RefundButton) =>
    class extends RefundButton {
        _onClick() {
            this.env.pos.is_ticket_screen_show = true;
            super._onClick();
        }
    };

const StockTicketScreen = (TicketScreen) =>
    class extends TicketScreen {
        _onCloseScreen() {
            this.env.pos.is_ticket_screen_show = false;
            super._onCloseScreen();
        }

        _onCreateNewOrder() {
            this.env.pos.is_ticket_screen_show = false;
            super._onCreateNewOrder();
        }

        _getToRefundDetail(orderline) {
            const line = super._getToRefundDetail(orderline);
            if (orderline && orderline.location_id) {
                line['orderline']['location_id'] = orderline.location_id;
            }
            return line;
        }

        async _onDoRefund() {
            const order = this.getSelectedSyncedOrder();
            if (!order) {
                this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
                return this.render();
            }

            if (this._doesOrderHaveSoleItem(order)) {
                this._prepareAutoRefundOnOrder(order);
            }

            const customer = order.get_client();
            const allToRefundDetails = Object.values(this.env.pos.toRefundLines).filter(({qty, orderline, destinationOrderUid}) => !this.env.pos.isProductQtyZero(qty) && (customer ? orderline.orderPartnerId == customer.id : true) && !destinationOrderUid
            );
            if (allToRefundDetails.length === 0) {
                this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
                return this.render();
            }

            const destinationOrder =
                this.props.destinationOrder && customer === this.props.destinationOrder.get_client() ? this.props.destinationOrder : this.env.pos.add_new_order({silent: true});

            for (const refundDetail of allToRefundDetails) {
                const {qty, orderline} = refundDetail;
                var product = this.env.pos.db.get_product_by_id(orderline.productId);
                product.added = true;
                await destinationOrder.add_product(product, {
                    quantity: -qty,
                    price: orderline.price,
                    lst_price: orderline.price,
                    extras: {price_manually_set: true},
                    merge: false,
                    refunded_orderline_id: orderline.id,
                    tax_ids: orderline.tax_ids,
                    discount: orderline.discount,
                    location_id: orderline.location_id,
                })
                refundDetail.destinationOrderUid = destinationOrder.uid;
            }

            if (customer && !destinationOrder.get_client()) {
                destinationOrder.set_client(customer);
            }
            this._onCloseScreen();
        }

        async _onBeforeDeleteOrder(order) {
            const self = this;
            const lines = order && order.get_orderlines();
            if (lines) {
                _.each(lines, function (line) {
                    if (line.location_id) {
                        var quant_by_product_id = self.env.pos.db.quant_by_product_id[line.product.id];
                        if (quant_by_product_id) {
                            if (self.env.pos.config.picking_type == 'quantity_available') {
                                quant_by_product_id[line.location_id]['quantity_available'] = quant_by_product_id[line.location_id]['quantity_available'] + line.quantity
                            } else if (self.env.pos.config.picking_type == 'quantity_unreserved') {
                                quant_by_product_id[line.location_id]['quantity_unreserved'] = quant_by_product_id[line.location_id]['quantity_unreserved'] + line.quantity
                            }
                        }
                    }
                });
            }
            return super._onBeforeDeleteOrder(order);
        }
    }

const StockProductsWidget = (ProductsWidget) =>
    class extends ProductsWidget {
        get productsToDisplay() {
            const self = this;
            const products = [];

            _.each(this.env.pos.db.search_product_in_category(this.selectedCategoryId, this.searchWord), function (product) {
                var quant_by_product_id = self.env.pos.db.quant_by_product_id[product.id];
                if (quant_by_product_id) {
                    product.quantity = 0;
                    $.each(quant_by_product_id, function (key, value) {
                        var warehouse = self.env.pos.db.warehouse_by_id[key];
                        if (warehouse) {
                            if (self.env.pos.config.warehouse_ids.includes(warehouse.id)) {
                                if (self.env.pos.config.picking_type == 'quantity_available') {
                                    product.quantity += value.quantity_available;
                                } else if (self.env.pos.config.picking_type == 'quantity_unreserved') {
                                    product.quantity += value.quantity_unreserved;
                                }
                            }
                        }
                    });

                } else {
                    product.quantity = 0;
                }
                products.push(product);
            });
            return products;
        }
    };

Registries.Component.extend(RefundButton, StockRefundButton);
Registries.Component.extend(TicketScreen, StockTicketScreen);
Registries.Component.extend(ProductsWidget, StockProductsWidget);
});
