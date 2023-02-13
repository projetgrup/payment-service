odoo.define('pos_stock.StockPopup', function (require) {
'use strict';

const { useState } = owl.hooks;
const Registries = require('point_of_sale.Registries');
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');

class StockPopup extends AbstractAwaitablePopup {

    constructor() {
        super(...arguments);
        this.mode = this.props.mode;
        this.title = this.props.title;
        this.product = this.props.product;
        this.config = this.env.pos.config;

        const transfers = {};
        this.props.warehouses.forEach(wh => {
            transfers[wh.id] = {
                location: wh.location,
                quantity: this.props.quantity || (this.props.default === wh.id ? 1 : ''),
                type: this.props.type || (this.props.default === wh.id ? 'immediately' : 'later'),
                method: this.props.method || 'shopping',
                date: this.props.date,
            }
        });

        this.state = useState({
            transfers: transfers,
        });
    }

    async getPayload() {
        var values = [];
        $.each(this.state.transfers, function (key, value) {
            if (value.quantity > 0) {
                values.push({
                    location_id: value.location,
                    quantity: value.quantity,
                    transfer_type: value.type,
                    transfer_method: value.method,
                    transfer_date: value.date,
                });
            }
        });
        return values;
    }

    onClickSelect(event) {
        const $btn = $(event.target).closest('button');
        if ($btn.data('type') === 'type') {
            this.state.transfers[$btn.data('id')].type = $btn.data('name');
        } else if ($btn.data('type') === 'method') {
            this.state.transfers[$btn.data('id')].method = $btn.data('name');
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
