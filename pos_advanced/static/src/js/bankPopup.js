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
            banks: []
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
            console.log(result);
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

    async sms(ev) {
        const $button = $(ev.target).closest('div.button');
        const $icon = $button.find('i');
        $button.addClass('disabled');
        $icon.toggleClass(['fa-commenting-o', 'fa-circle-o-notch', 'fa-spin']);
        try {
            const $phone = document.getElementById('jetcheckout_link_phone');
            if ($phone.value == '') {
                this.showNotificationDanger(_t('Please fill phone number'));
                return;
            }
            const result = await this.env.session.rpc('/pos/link/sms', {
                partner: this.props.partner,
                url: this.transaction.url,
                amount: this.line.amount,
                currency: this.env.pos.currency.id,
                phone: $phone.value,
            });
            this.showNotificationSuccess(result);
        } catch (error) {
            console.error(error);
            Gui.showPopup('ErrorPopup', {
                title: _t('SMS Sending Error'),
                body: _t('SMS could not be sent. Please try again.'),
            });
        }
        $button.removeClass('disabled');
        $icon.toggleClass(['fa-commenting-o', 'fa-circle-o-notch', 'fa-spin']);
    }

    async email(ev) {
        const $button = $(ev.target).closest('div.button');
        const $icon = $button.find('i');
        $button.addClass('disabled');
        $icon.toggleClass(['fa-envelope-o', 'fa-circle-o-notch', 'fa-spin']);
        try {
            const $email = document.getElementById('jetcheckout_link_email');
            if ($email.value == '') {
                this.showNotificationDanger(_t('Please fill email address'));
                return;
            }
            const result = await this.env.session.rpc('/pos/link/email', {
                partner: this.props.partner,
                url: this.transaction.url,
                amount: this.line.amount,
                currency: this.env.pos.currency.id,
                email: $email.value,
            });
            this.showNotificationSuccess(result);
        } catch (error) {
            console.error(error);
            Gui.showPopup('ErrorPopup', {
                title: _t('Email Sending Error'),
                body: _t('Email could not be sent. Please try again.'),
            });
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
