odoo.define('pos_advanced.AddressPopup', function(require) {
'use strict';

const { useState } = owl.hooks;
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
var core = require('web.core');

var _t = core._t;

class AddressPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.partner = this.props.partner;
        this.child = this.props.child;
        this.state = useState({
            type: this.child && this.child.type || 'delivery',
            name: this.child && this.child.name || '',
            street: this.child && this.child.street || '',
            city: this.child && this.child.city || '',
            zip: this.child && this.child.zip || '',
            state: this.child && this.child.state || '',
            country: this.child && this.child.country || '',
            email: this.child && this.child.email || '',
            phone: this.child && this.child.phone || '',
            mobile: this.child && this.child.mobile || '',
            comment: this.child && this.child.comment && $('<div>' + this.child.comment + '</div>').text() || '',
        });
    }

    showNotificationSuccess(message) {
        const duration = 2001;
        this.trigger('show-notification', { message, duration });
    }

    showNotificationDanger(message) {
        const duration = 2002;
        this.trigger('show-notification', { message, duration });
    }

    selectType(ev) {
        const $radio = $(ev.target).closest('div.address-radio');
        const $input = $radio.find('input');
        $input.prop('checked', true);
        this.state.delivery = $radio.prop('name');
        console.log(this.state);
    }

    async create(ev) {
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

}

AddressPopup.template = 'AddressPopup';
AddressPopup.defaultProps = {
    title: _t('Address Information'),
};

Registries.Component.add(AddressPopup);

return AddressPopup;
});
