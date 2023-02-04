/** @odoo-module **/

import TicketButton from 'point_of_sale.TicketButton';
import Registries from 'point_of_sale.Registries';
import { posbus } from 'point_of_sale.utils';

export const TicketButtonSync = (TicketButton) => 
    class TicketButtonSync extends TicketButton {
        syncedOrderCompleted() {
            this.showScreen('TicketScreen');
            this.showNotification(this.env._t('This order has been completed by owner cashier'), 2001);
        }

        willPatch() {
            super.willPatch();
            posbus.off('synced-order-completed', this);
        }
        patched() {
            super.patched();
            posbus.on('synced-order-completed', this, this.syncedOrderCompleted);
        }
        mounted() {
            super.mounted();
            posbus.on('synced-order-completed', this, this.syncedOrderCompleted);
        }
        willUnmount() {
            super.willUnmount();
            posbus.off('synced-order-completed', this);
        }

    };

Registries.Component.extend(TicketButton, TicketButtonSync)