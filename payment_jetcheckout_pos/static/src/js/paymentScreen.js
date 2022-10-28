/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';

export const JetcheckoutPaymentScreen = (PaymentScreen) => 
    class JetcheckoutPaymentScreen extends PaymentScreen {
        constructor() {
            super(...arguments);
            this.vpos_acquirer = this.env.pos.vpos_acquirer;
            this.vpos_card_types = this.env.pos.vpos_card_types;
            this.vpos_card_families = this.env.pos.vpos_card_families;
        }
        
        async showInstallments() {
            await this.showPopup('InstallmentPopup', {
                title: this.env._t('Installment Table'),
                acquirer: this.vpos_acquirer,
            });
        }
    };

Registries.Component.extend(PaymentScreen, JetcheckoutPaymentScreen)