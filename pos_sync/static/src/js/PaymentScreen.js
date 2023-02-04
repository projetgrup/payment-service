/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';

export const PaymentScreenSync = (PaymentScreen) => 
    class PaymentScreenSync extends PaymentScreen {
        get nextScreen() {
            this.currentOrder.stop_syncing();
            return !this.error ? 'ReceiptScreen' : 'ProductScreen';
        }
    };

Registries.Component.extend(PaymentScreen, PaymentScreenSync)