odoo.define('pos_sync.SyncButton', function (require) {
'use strict';

const PosComponent = require('point_of_sale.PosComponent');
const Registries = require('point_of_sale.Registries');
const { posbus } = require('point_of_sale.utils');

class SyncButton extends PosComponent {
    onClick() {
        if (this.env.pos) {
            const order = this.env.pos.get_order();
            if (order) {
                if (order.is_syncing()) {
                    order.stop_syncing();
                } else {
                    order.start_syncing();
                }
                order.need_synced();
                this.render();
            }
        }
    }

    willPatch() {
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
    }

    get syncOk() {
        if (this.env.pos) {
            return this.env.pos.sync_ok;
        } else {
            return false;
        }
    }

    get owner() {
        if (this.env.pos) {
            const order = this.env.pos.get_order();
            return order && order.is_owner();
        } else {
            return true;
        }
    }

    get syncing() {
        if (this.env.pos) {
            const order = this.env.pos.get_order();
            return order && order.is_syncing();
        } else {
            return false;
        }
    }
}

SyncButton.template = 'SyncButton';

Registries.Component.add(SyncButton);

return SyncButton;
});
