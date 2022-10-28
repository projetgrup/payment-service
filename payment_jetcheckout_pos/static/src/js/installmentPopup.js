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
            this.installments = await this.env.session.rpc('/payment/card/installments', {
                acquirer: this.props.acquirer.id,
                list: true,
            });
            if ('error' in this.installments) {
                this.error = this.installments.error;
            }
            console.log(this.installments);
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
