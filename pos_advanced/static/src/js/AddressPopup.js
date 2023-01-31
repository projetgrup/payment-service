odoo.define('pos_advanced.AddressPopup', function(require) {
'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
var core = require('web.core');

var _t = core._t;

class AddressPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.order = this.props.order;
        this.partner = this.props.partner;
        this.address = this.props.address;
        this.type = this.props.type;
        this.state = {
            id: this.address && this.address.id || false,
            name: this.address && this.address.name || '',
            street: this.address && this.address.street || '',
            city: this.address && this.address.city || '',
            zip: this.address && this.address.zip || '',
            email: this.address && this.address.email || '',
            phone: this.address && this.address.phone || '',
            mobile: this.address && this.address.mobile || '',
            comment: this.address && this.address.comment && $('<div>' + this.address.comment + '</div>').text() || '',
            type: this.address ? this.address.type : this.type || 'delivery',
            sequence: this.address ? this.address.sequence : this.props.sequence,
            state_id: this.address ? this.address.state_id : this.env.pos.config.partner_address_state_id || false,
            country_id: this.address ? this.address.country_id : this.env.pos.config.partner_address_country_id || false,
        };
    }

    changeType(ev) {
        const $radio = $(ev.target).closest('div.address-radio');
        const $input = $radio.find('input');
        $input.prop('checked', true);
        this.state.type = $input.val();
    }

    changeState(ev) {
        const id = parseInt(ev.target.value);
        if (!id) {
            this.state.state_id = false;
        } else {
            const state = this.env.pos.states.find(s => s.id === id);
            this.state.state_id = [id, state ? state.name : ''];
        }
        this.render();
    }

    changeCountry(ev) {
        const id = parseInt(ev.target.value);
        if (!id) {
            this.state.country_id = false;
        } else {
            const country = this.env.pos.countries.find(s => s.id === id);
            this.state.country_id = [id, country ? country.name : ''];
        }
        this.render();
    }

    async getPayload() {
        const self = this.state;
        const address = (self.street ? self.street + ', ': '') +
                        (self.zip ? self.zip + ', ': '') +
                        (self.city ? self.city + ', ': '') +
                        (self.state_id ? self.state_id[1] + ', ': '') +
                        (self.country_id ? self.country_id[1]: '');
        return {address: address, ...this.state};
    }
}

AddressPopup.template = 'AddressPopup';
AddressPopup.defaultProps = {
    title: _t('Address Information'),
};

Registries.Component.add(AddressPopup);

return AddressPopup;
});
