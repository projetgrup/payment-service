odoo.define('pos_advanced.BankPopup', function(require) {
'use strict';

const { useState } = owl.hooks;
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const { Gui } = require('point_of_sale.Gui');
var core = require('web.core');

var _t = core._t;

class BankPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.partner = undefined;
        this.banks = undefined;
        this.state = useState({
            email: '',
            phone: '',
            banks: [],
        });
    }

    async willStart() {
        try {
            const result = await this.env.session.rpc('/pos/bank/prepare', {
                partner: this.props.partner,
                banks: this.props.banks,
            });
            this.partner = result.partner;
            this.banks = result.banks;
            this.state.banks = _.pluck(result.banks, 'id');
            this.state.email = this.partner.email;
            this.state.phone = this.partner.phone;
            if ('error' in result) {
                throw result.error;
            }
        } catch (error) {
            console.error(error);
            Gui.showPopup('ErrorPopup', {
                title: _t('Network Error'),
                body: _t('Bank information cannot be retrieved. Please check your connection or contact with your system administrator.'),
            });
        }
    }

    showNotificationSuccess(message) {
        const duration = 2001;
        this.trigger('show-notification', { message, duration });
    }

    showNotificationDanger(message) {
        const duration = 2002;
        this.trigger('show-notification', { message, duration });
    }

    toggleBank(id) {
        if (this.state.banks.includes(id)) {
            this.state.banks = this.state.banks.filter(bid => bid !== id);
        } else {
            this.state.banks.push(id);
        }
    }

    async sendSms(ev) {
        const $button = $(ev.target).closest('div.button');
        const $icon = $button.find('i');
        $button.addClass('disabled');
        $icon.toggleClass(['fa-commenting-o', 'fa-circle-o-notch', 'fa-spin']);
        try {
            if (this.state.phone == '') {
                this.showNotificationDanger(_t('Please fill phone number'));
            } else {
                const result = await this.env.session.rpc('/pos/bank/sms', {
                    partner: this.partner.id,
                    banks: this.state.banks,
                    phone: this.state.phone,
                });
                this.showNotificationSuccess(result);
            }
        } catch (error) {
            console.error(error);
            this.showNotificationDanger(_t('SMS has not been sent'));
        }
        $button.removeClass('disabled');
        $icon.toggleClass(['fa-commenting-o', 'fa-circle-o-notch', 'fa-spin']);
    }

    async sendEmail(ev) {
        const $button = $(ev.target).closest('div.button');
        const $icon = $button.find('i');
        $button.addClass('disabled');
        $icon.toggleClass(['fa-envelope-o', 'fa-circle-o-notch', 'fa-spin']);
        try {
            if (this.state.email == '') {
                this.showNotificationDanger(_t('Please fill email address'));
            } else if (!this.state.banks.length) {
                this.showNotificationDanger(_t('Please select at least one bank'));
            } else {
                const result = await this.env.session.rpc('/pos/bank/email', {
                    partner: this.partner.id,
                    banks: this.state.banks,
                    email: this.state.email,
                });
                this.showNotificationSuccess(result);
            }
        } catch (error) {
            console.error(error);
            this.showNotificationDanger(_t('Email has not been sent'));
        }
        $button.removeClass('disabled');
        $icon.toggleClass(['fa-envelope-o', 'fa-circle-o-notch', 'fa-spin']);
    }

}

BankPopup.template = 'BankPopup';
BankPopup.defaultProps = {
    title: _t('Bank Information'),
};

Registries.Component.add(BankPopup);

return BankPopup;
});
