odoo.define('pos_jetcheckout.InstallmentPopup', function(require) {
'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const { Gui } = require('point_of_sale.Gui');
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
                throw this.installments.error;
            }
        } catch (error) {
            console.error(error);
            Gui.showPopup('ErrorPopup', {
                title: _t('Network Error'),
                body: _t('Installment table could not be accessable. Please check your connection.'),
            });
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
