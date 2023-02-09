odoo.define('pos_stock.StockPopup', function (require) {
'use strict';

const { useState } = owl.hooks;
const Registries = require('point_of_sale.Registries');
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');

class StockPopup extends AbstractAwaitablePopup {

    constructor() {
        super(...arguments);
        this.title = this.props.title;
        this.product = this.props.product;
        this.config = this.env.pos.config;

        const date = new Date();
        date.setDate(date.getDate() + this.env.pos.config.picking_day_threshold);
        const dateStr = date.toISOString().slice(0,10)

        const transfers = {};
        this.props.warehouses.forEach(wh => {
            transfers[wh.warehouse_id] = {
                type: this.props.warehouse_id === wh.warehouse_id ? 'immediately' : 'later',
                location: 'shopping',
                date: dateStr,
            }
        });

        this.state = useState({
            transfers: transfers,
        });
    }

    onClickSelect(event) {
        const $btn = $(event.target).closest('button');
        if ($btn.data('type') === 'type') {
            this.state.transfers[$btn.data('id')].type = $btn.data('name');
        } else if ($btn.data('type') === 'location') {
            this.state.transfers[$btn.data('id')].location = $btn.data('name');
        }
    }

    onKeyupQty(event) {
        if (!this.env.pos.config.picking_negative_ok) {
            var quantity = $(event.currentTarget).closest('tr').find('.input-available')[0].innerText;
            if (parseInt($(event.currentTarget)[0].value) > parseInt(quantity)) {
                $(event.currentTarget)[0].classList.add('add-quantity');
                $(event.currentTarget)[0].value = '';
            } else {
                $(event.currentTarget)[0].classList.remove('add-quantity');
            }
        }
    }

    mounted() {
        super.mounted()
        const $input = $('.input-quantity');
        $input.focus();
        $input.keyup(function () {
            this.value = this.value.replace(/[^0-9\.]/g, '');
        });
    }

    async add() {
        var self = this;
        var order = this.env.pos.get_order();

        _.each($('input.input-quantity'), async function (input) {
            const $row = $(input).closest('tr');
            if (input.value) {
                var product = self.env.pos.db.get_product_by_id(self.product);
                var location_id = $row.data('id');
                var transfer_type = $row.find('input.transfer-type');
                var transfer_date = $row.find('input.transfer-date');
                var transfer_location = $row.find('.transfer_location');

                if (product) {
                    product.added = true;
                    order.temp = true;
                    await order.add_product(product, {
                        quantity: each_input_value.value,
                        location_id: location_id.value,
                        transfer_type: transfer_type.val() === '-1' ? false : transfer_type.val(),
                        transfer_location: transfer_location.val() === '-1' ? false : transfer_location.val(),
                        transfer_date: transfer_date.val() == '' ? false : transfer_date.val(),
                        merge: false,
                    })
                    product.temp = false;
                }
            }
        });
        order.temp = false;
        this.trigger('close-popup');
    }
}

StockPopup.template = 'StockPopup';
Registries.Component.add(StockPopup);
return StockPopup;
});
