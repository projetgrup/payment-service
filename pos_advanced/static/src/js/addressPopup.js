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
        this.intFields = ['country_id', 'state_id'];
        this.changes = {
            'country_id': this.partner.country_id && this.partner.country_id[0],
            'state_id': this.partner.state_id && this.partner.state_id[0],
        };
        this.state = useState({
            email: '',
            phone: '',
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

    captureChange(event) {
        this.changes[event.target.name] = event.target.value;
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
