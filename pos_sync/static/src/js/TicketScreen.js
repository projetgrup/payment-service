/** @odoo-module **/

import TicketScreen from 'point_of_sale.TicketScreen';
import Registries from 'point_of_sale.Registries';

export const TicketScreenSync = (TicketScreen) => 
    class TicketScreenSync extends TicketScreen {
        async _onBeforeDeleteOrder(order) {
            await order.stop_syncing();
            return super._onBeforeDeleteOrder(order);
        }

        shouldHideDeleteButton(order) {
            const res = super.shouldHideDeleteButton(order);
            return res || !order.is_owner();
        }

        shouldHideSyncButton(order) {
            return order.locked || order.is_owner();
        }
    };

Registries.Component.extend(TicketScreen, TicketScreenSync)