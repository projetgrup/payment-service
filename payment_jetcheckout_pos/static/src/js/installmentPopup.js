odoo.define('payment_jetcheckout_pos.InstallmentPopup', function(require) {
'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');

class InstallmentPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
    }

    async willStart() {
        try {
            const order = this.env.pos.get_order();
            this.amount = order.get_total_with_tax();
            this.installments = await this.env.session.rpc('/payment/card/installments', {
                list: true,
                acquirer: this.props.acquirer.id,
                amount: this.amount,
            });
            if ('error' in this.installments) {
                this.error = this.installments.error;
            }
        } catch (error) {
            this.error = error;
        }
    }

    mounted() {
        if (this.error) {
            this.cancel();
            this.showPopup('ErrorPopup', {
                title: this.env._t('Network Error'),
                body: this.env._t('Cannot access installment table. Please check your connection.'),
            });
            throw this.error;
        }
    }
}

InstallmentPopup.template = 'InstallmentPopup';
InstallmentPopup.defaultProps = {
    title: '',
};

Registries.Component.add(InstallmentPopup);

return InstallmentPopup;
});
