odoo.define('pos_jetcheckout.LinkPopup', function(require) {
'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const Cards = require('payment_jetcheckout.cards');
var core = require('web.core');

var _t = core._t;

class JetcheckoutLinkPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.line = this.props.line;
    }

    async willStart() {
        try {
            this.partner = await this.env.session.rpc('/pos/link/prepare', {
                partner: this.props.partner,
                method: this.line.payment_method.id,
                amount: this.line.amount,
            });
            if ('error' in this.partner) {
                throw this.partner.error;
            }
        } catch (error) {
            console.error(error);
            this.showPopup('ErrorPopup', {
                title: _t('Network Error'),
                body: _t('Cannot access partner information. Please check your connection.'),
            });
        }
    }

    showPopup(name, props) {
        if (name === 'ErrorPopup') {
            this.line.set_payment_status('retry');
        }
        return super.showPopup(...arguments);
    }

}

JetcheckoutLinkPopup.template = 'JetcheckoutLinkPopup';
JetcheckoutLinkPopup.defaultProps = {
    title: _t('Link Information'),
};

Registries.Component.add(JetcheckoutLinkPopup);

return JetcheckoutLinkPopup;
});
