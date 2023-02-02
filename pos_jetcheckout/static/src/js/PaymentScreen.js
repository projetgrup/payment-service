/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';
import { useListener } from 'web.custom_hooks';

export const JetcheckoutPaymentScreen = (PaymentScreen) => 
    class JetcheckoutPaymentScreen extends PaymentScreen {

        constructor() {
            super(...arguments);
            useListener('select-electronic-payment-line', this._selectElectronicPaymentLine);
            useListener('add-payment-transaction', this._addPaymentTransaction);
            this.jetcheckout = this.env.pos.jetcheckout;
        }

        async _selectElectronicPaymentLine(event) {
            const { cid } = event.detail;
            const line = this.paymentLines.find((line) => line.cid === cid);
            if (line && line.payment_method.use_payment_terminal === 'jetcheckout_link' && line.payment_status === 'waiting') {
                await line.payment_method.payment_terminal._jetcheckout_pay(cid);
            }
        }

        async _addPaymentTransaction(event) {
            const partner = this.currentOrder.get_client();
            if (!partner) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please select a customer'),
                });
                return;
            }

            const { cid } = event.detail;
            const line = this.paymentLines.find((line) => line.cid === cid);
            if (line) {
                const { confirmed, payload: transaction } = await this.showTempScreen(
                    'TransactionListScreen',
                    { partner: partner, line: line }
                );
                if (confirmed) {
                    line.remove_transaction();
                    line.set_payment_status('done');
                    line.set_amount(transaction.amount);
                    line.transaction_id = transaction.id;
                    this.currentOrder.transaction_ids.push(transaction.id);
                }
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