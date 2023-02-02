odoo.define('pos_advanced.SyncButton', function (require) {
'use strict';

const PosComponent = require('point_of_sale.PosComponent');
const Registries = require('point_of_sale.Registries');
const { posbus } = require('point_of_sale.utils');

class SyncButton extends PosComponent {
    onClick() {
        if (this.env.pos) {
            const order = this.env.pos.get_order();
            if (order) {
                order.in_sync = !order.in_sync;
                this.render();
                console.log(order);
            }
        }

        /*if (this.props.inSync) {
            posbus.trigger('ticket-button-clicked');
        } else {
            this.showScreen('TicketScreen');
        }*/
    }
    /*willPatch() {
        posbus.off('order-deleted', this);
    }
    patched() {
        posbus.on('order-deleted', this, this.render);
    }
    mounted() {
        posbus.on('order-deleted', this, this.render);
    }
    willUnmount() {
        posbus.off('order-deleted', this);
    }*/
    get inSync() {
        if (this.env.pos) {
            const order = this.env.pos.get_order();
            return order && order.in_sync;
        } else {
            return false;
        }
    }
}

SyncButton.template = 'SyncButton';

Registries.Component.add(SyncButton);

return SyncButton;
});
