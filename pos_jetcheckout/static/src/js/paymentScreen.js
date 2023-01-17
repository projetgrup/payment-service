/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';
import { Gui } from 'point_of_sale.Gui';
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

        async _isOrderValid() {
            if (this.env.pos.config.jetcheckout_cash_payment_limit_ok) {
                const cashLines = this.paymentLines.filter(payment => payment.payment_method.is_cash_count);
                const cashTotal = cashLines.reduce((sum, line) => sum + line.amount, 0);
                const cashLimit = this.env.pos.config.jetcheckout_cash_payment_limit_amount;
                if (cashTotal > cashLimit) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Cash Payment Amount Exceeded'),
                        body: _.str.sprintf(this.env._t('Cash payment amount cannot be higher than %s for this shop.'), this.env.pos.format_currency(cashLimit)),
                    });
                    return false;
                }
            }
            return super._isOrderValid(...arguments);
        }

    };

Registries.Component.extend(PaymentScreen, JetcheckoutPaymentScreen)