/** @odoo-module **/

import TicketScreen from 'point_of_sale.TicketScreen';
import Registries from 'point_of_sale.Registries';
import { useListener } from 'web.custom_hooks';

export const PosTicketScreen = (TicketScreen) => 
    class PosTicketScreen extends TicketScreen {
        constructor() {
            super(...arguments);
            useListener('remove-refund-order-uid', this._onRemoveRefundOrderUid);
        }

        _onRemoveRefundOrderUid({detail: uid, originalComponent: self}) {
            const refundOrder = this.env.pos.get('orders').models.find((order) => order.uid == uid);
            if (refundOrder) {
                refundOrder.destroy({'reason':'abandon'});
            }
            delete this.env.pos.toRefundLines[self.props.line.id];
            this.render();
        }
    };

Registries.Component.extend(TicketScreen, PosTicketScreen);
