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
            transfers[wh.id] = {
                type: this.props.default === wh.id ? 'immediately' : 'later',
                location: 'shopping',
                date: dateStr,
            }
        });

        this.state = useState({
            transfers: transfers,
        });
    }

    async getPayload() {
        var values = [];
        _.each($('input.input-quantity'), async function (input) {
            const $row = $(input).closest('tr');
            if (input.value) {
                var location_id = $row.data('id');
                var transfer_type = $row.find('input.transfer-type');
                var transfer_date = $row.find('input.transfer-date');
                var transfer_location = $row.find('input.transfer-location');
                values.push({
                    quantity: input.value,
                    location_id: location_id,
                    transfer_type: transfer_type.val() === '-1' ? false : transfer_type.val(),
                    transfer_location: transfer_location.val() === '-1' ? false : transfer_location.val(),
                    transfer_date: transfer_date.val() == '' ? false : transfer_date.val(),
                    merge: false,
                });
            }
        });
        return values;
    }

    onClickSelect(event) {
        const $btn = $(event.target).closest('button');
        if ($btn.data('type') === 'type') {
            this.state.transfers[$btn.data('id')].type = $btn.data('name');
        } else if ($btn.data('type') === 'location') {
            this.state.transfers[$btn.data('id')].location = $btn.data('name');
        }
    }

    onKeyupQuantity(event) {
        if (!this.env.pos.config.picking_negative_ok) {
            const $input = $(event.currentTarget);
            const quantity = $input.closest('tr').find('td.input-available').text();
            if (parseInt($input.val()) > parseInt(quantity)) {
                $input.addClass('add-quantity');
                $input.val('');
            } else {
                $input.removeClass('add-quantity');
            }
        }
    }

    mounted() {
        super.mounted()
        const $input = $('input.input-quantity');
        $input.focus();
        $input.keyup(function () {
            this.value = this.value.replace(/[^0-9\.]/g, '');
        });
    }
}

StockPopup.template = 'StockPopup';
Registries.Component.add(StockPopup);
return StockPopup;
});
