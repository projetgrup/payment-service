odoo.define('pos_jetcheckout.InstallmentPopup', function(require) {
'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
var core = require('web.core');

var _t = core._t;

class InstallmentPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.amount = this.props.amount;
    }

    async willStart() {
        try {
            this.installments = await this.env.session.rpc('/payment/card/installments', {
                list: true,
                acquirer: this.env.pos.jetcheckout.acquirer.id,
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
    title: _t('Installment Table'),
};

Registries.Component.add(InstallmentPopup);

return InstallmentPopup;
});
