odoo.define('pos_stock.Components', function (require) {
'use strict';

const NumberBuffer = require('point_of_sale.NumberBuffer');
const Orderline = require('point_of_sale.Orderline');
const ProductScreen = require('point_of_sale.ProductScreen');
const ProductsWidget = require('point_of_sale.ProductsWidget');
const Registries = require('point_of_sale.Registries');
const TicketScreen = require('point_of_sale.TicketScreen');
const ErrorPopup = require('point_of_sale.ErrorPopup');
const { posbus } = require('point_of_sale.utils');
const { useListener } = require('web.custom_hooks');


const StockOrderline = (Orderline) =>
    class extends Orderline {
        configureLine() {
            this.props.line.order.set_product(this.props.line);
        }
    }

const StockTicketScreen = (TicketScreen) =>
    class extends TicketScreen {
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
    }

const StockProductScreen = (ProductScreen) =>
    class extends ProductScreen {
        constructor() {
            super(...arguments);
            useListener('right-click-product', this._rightClickProduct);
        }

        async _rightClickProduct(event) {
            event.preventDefault();
            event.stopPropagation();
            if (!this.currentOrder) this.env.pos.add_new_order();
            const product = event.detail;
            const options = await this._getAddProductOptions(product);
            if (!options) return;
            options.forceOpen = true;
            this.currentOrder.add_product(product, options);
            NumberBuffer.reset();
        }
    }

const StockProductsWidget = (ProductsWidget) =>
    class extends ProductsWidget {
        willPatch() {
            super.willPatch();
            posbus.off('render-product-list', this);
        }

        patched() {
            super.patched();
            posbus.on('render-product-list', this, this._renderProductList);
        }

        mounted() {
            super.mounted();
            posbus.on('render-product-list', this, this._renderProductList);
        }

        willUnmount() {
            super.willUnmount();
            posbus.off('render-product-list', this);
        }

        _renderProductList() {
            this.render();
        }

        get productsToDisplay() {
            const db = this.env.pos.db;
            const products = [];

            _.each(db.search_product_in_category(this.selectedCategoryId, this.searchWord), function (product) {
                const quant = db.quant_by_product_id[product.id];
                product.quantity = 0;
                $.each(quant, function (key, value) {
                    product.quantity += value;
                });
                products.push(product);
            });
            return products;
        }
    };

const StockErrorPopup = (ErrorPopup) =>
    class extends ErrorPopup {
        mounted() {
            if (this.props.silent) {
                return;
            }
            super.mounted();
        }
    };

Registries.Component.extend(Orderline, StockOrderline);
Registries.Component.extend(TicketScreen, StockTicketScreen);
Registries.Component.extend(ProductScreen, StockProductScreen);
Registries.Component.extend(ProductsWidget, StockProductsWidget);
Registries.Component.extend(ErrorPopup, StockErrorPopup);
});
