odoo.define('pos_jetcheckout.LinkPopup', function(require) {
'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const { Gui } = require('point_of_sale.Gui');
var rpc = require('web.rpc');
var core = require('web.core');

var _t = core._t;

class JetcheckoutLinkPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.line = this.props.line;
        this.order = this.props.order;
        this.partner = undefined;
        this.duration = undefined;
        this.interval = undefined;
    }

    async willStart() {
        try {
            this.partner = await this.env.session.rpc('/pos/link/prepare', {
                partner: this.props.partner,
                acquirer: this.env.pos.jetcheckout.acquirer.id,
                method: this.line.payment_method.id,
                amount: this.line.amount,
                order: {
                    id: this.order.uid,
                    name: this.order.name,
                }
            });
            if ('error' in this.partner) {
                throw this.partner.error;
            }
            this.duration = this.partner.duration;
            this.order.transaction_id = this.partner.tx;
        } catch (error) {
            clearInterval(this.interval);
            this.line.set_payment_status('retry');
            console.error(error);
            Gui.showPopup('ErrorPopup', {
                title: _t('Network Error'),
                body: _t('Payment link could not be created. Please check your connection or contact with your system administrator.'),
            });
        }
    }

    mounted() {
        const self = this;
        const order = this.order;
        this.$countdown = document.getElementById('jetcheckout_link_countdown');
        this.interval = setInterval(function() {
            if (self.duration === 0) {
                clearInterval(self.interval);
                order.transaction_id = 0;
                self.line.set_payment_status('timeout');
                self.trigger('close-popup');
                return;
            }

            if (self.duration % 5 === 0) {
                rpc.query({
                    route: '/pos/link/query',
                    params: {tx: order.transaction_id}
                }, {timeout: 1000}).then(function (result) {
                    if (result.status === 0) {
                        clearInterval(self.interval);
                        order.transaction_id = 0;
                        self.line.set_payment_status('done');
                        self.trigger('close-popup');
                        return;
                    } else if (result.status === -1) {
                        clearInterval(self.interval);
                        order.transaction_id = 0;
                        self.showPopup('ErrorPopup', {
                            title: _t('Error'),
                            body: result.message || _t('An error occured. Please try again.'),
                        });
                        return;
                    }
                }).catch(function(error) {
                    console.error(error);
                });
            }
            self.duration -= 1;
            self.$countdown.innerHTML = self.duration;
        }, 1000);
    }

    showPopup(name, props) {
        if (name === 'ErrorPopup') {
            clearInterval(this.interval);
            this.line.set_payment_status('retry');
        }
        return super.showPopup(...arguments);
    }

    copy() {
        navigator.clipboard.writeText(this.partner.url);
    }

    async sms(ev) {
        const $button = $(ev.target).closest('div.button');
        const $icon = $button.find('i');
        $button.addClass('disabled');
        $icon.toggleClass(['fa-commenting-o', 'fa-circle-o-notch', 'fa-spin']);
        try {
            const $phone = document.getElementById('jetcheckout_link_phone');
            if ($phone.value == '') {
                this.showNotification(_t('Please fill phone number'));
                return;
            }
            const result = await this.env.session.rpc('/pos/link/sms', {
                partner: this.props.partner,
                url: this.partner.url,
                amount: this.line.amount,
                currency: this.env.pos.currency.id,
                phone: $phone.value,
            });
            this.showNotification(result);
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
                this.showNotification(_t('Please fill email address'));
                return;
            }
            const result = await this.env.session.rpc('/pos/link/email', {
                partner: this.props.partner,
                url: this.partner.url,
                amount: this.line.amount,
                currency: this.env.pos.currency.id,
                email: $email.value,
            });
            this.showNotification(result);
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

JetcheckoutLinkPopup.template = 'JetcheckoutLinkPopup';
JetcheckoutLinkPopup.defaultProps = {
    title: _t('Link Information'),
};

Registries.Component.add(JetcheckoutLinkPopup);

return JetcheckoutLinkPopup;
});
