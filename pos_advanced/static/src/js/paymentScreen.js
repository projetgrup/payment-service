/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';

export const PosPaymentScreen = (PaymentScreen) => 
    class PosPaymentScreen extends PaymentScreen {

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

Registries.Component.extend(PaymentScreen, PosPaymentScreen)
