/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';
import { useListener } from 'web.custom_hooks';

export const JetcheckoutPaymentScreen = (PaymentScreen) => 
    class JetcheckoutPaymentScreen extends PaymentScreen {

        constructor() {
            super(...arguments);
            useListener('select-electronic-payment-line', this.selectElectronicPaymentLine);
            this.jetcheckout = this.env.pos.jetcheckout;
        }

        async selectElectronicPaymentLine(event) {
            const { cid } = event.detail;
            const line = this.paymentLines.find((line) => line.cid === cid);
            if (line && line.payment_method.use_payment_terminal === 'jetcheckout_link' && line.payment_status === 'waiting') {
                await line.payment_method.payment_terminal._jetcheckout_pay(cid);
            }
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