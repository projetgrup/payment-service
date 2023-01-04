/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';

export const JetcheckoutPaymentScreen = (PaymentScreen) => 
    class JetcheckoutPaymentScreen extends PaymentScreen {

        constructor() {
            super(...arguments);
            this.jetcheckout = this.env.pos.jetcheckout;
        }

        async showCardInstallments() {
            $('.installment-button').addClass('disabled');
            const amount = this.currentOrder.get_due();
            await this.showPopup('InstallmentPopup', {
                amount: amount > 0 ? amount : 0
            });
            $('.installment-button').removeClass('disabled');
        }

    };

Registries.Component.extend(PaymentScreen, JetcheckoutPaymentScreen)