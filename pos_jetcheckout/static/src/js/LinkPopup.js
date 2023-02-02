odoo.define('pos_jetcheckout.LinkPopup', function(require) {
'use strict';

const { useState } = owl.hooks;
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const { Gui } = require('point_of_sale.Gui');
var core = require('web.core');

var _t = core._t;

class JetcheckoutLinkPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.line = this.props.line;
        this.order = this.props.order;
        this.transaction = undefined;
        this.state = useState({
            duration: this.line.duration,
        });
    }

    async willStart() {
        this.line.popup = this;
        if (!this.line.transaction) {
            try {
                const transaction = await this.env.session.rpc('/pos/link/prepare', {
                    acquirer: this.env.pos.jetcheckout.acquirer.id,
                    partner: this.props.partner,
                    method: this.line.payment_method.id,
                    amount: this.line.amount,
                    duration: this.props.duration || 0,
                    order: {
                        id: this.order.uid,
                        name: this.order.name,
                    }
                });
                if ('error' in transaction) {
                    throw transaction.error;
                }
                this.line.transaction = transaction;
                this.line.transaction_id = transaction.id;
            } catch (error) {
                console.error(error);
                this.line.popup = undefined;
                Gui.showPopup('ErrorPopup', {
                    title: _t('Network Error'),
                    body: _t('Payment link could not be created. Please check your connection or contact with your system administrator.'),
                });
            }
        }

        this.transaction = this.line.transaction;
        if (!this.transaction) {
            this.transaction = {};
        }
    }

    showPopup(name, props) {
        if (name === 'ErrorPopup') {
            this.line.remove_transaction();
            this.cancel();
        }
        return super.showPopup(...arguments);
    }

    showNotificationSuccess(message) {
        const duration = 2001;
        this.trigger('show-notification', { message, duration });
    }

    showNotificationDanger(message) {
        const duration = 2002;
        this.trigger('show-notification', { message, duration });
    }

    cancel() {
        this.line.payment_method.payment_terminal.send_payment_cancel(this.order, this.line.cid);
        super.cancel(...arguments);
    }

    close() {
        this.trigger('close-popup');
    }

    copyLink() {
        navigator.clipboard.writeText(this.transaction.url);
    }

    async sendSms(ev) {
        const $button = $(ev.target).closest('div.button');
        const $icon = $button.find('i');
        $button.addClass('disabled');
        $icon.toggleClass(['fa-commenting-o', 'fa-circle-o-notch', 'fa-spin']);
        try {
            const $phone = document.getElementById('jetcheckout_link_phone');
            if ($phone.value == '') {
                this.showNotificationDanger(_t('Please fill phone number'));
            } else {
                const result = await this.env.session.rpc('/pos/link/sms', {
                    partner: this.props.partner,
                    url: this.transaction.url,
                    amount: this.line.amount,
                    currency: this.env.pos.currency.id,
                    phone: $phone.value,
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
            const $email = document.getElementById('jetcheckout_link_email');
            if ($email.value == '') {
                this.showNotificationDanger(_t('Please fill email address'));
            } else {
                const result = await this.env.session.rpc('/pos/link/email', {
                    partner: this.props.partner,
                    url: this.transaction.url,
                    amount: this.line.amount,
                    currency: this.env.pos.currency.id,
                    email: $email.value,
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

JetcheckoutLinkPopup.template = 'JetcheckoutLinkPopup';
JetcheckoutLinkPopup.defaultProps = {
    title: _t('Link Information'),
};

Registries.Component.add(JetcheckoutLinkPopup);

return JetcheckoutLinkPopup;
});
