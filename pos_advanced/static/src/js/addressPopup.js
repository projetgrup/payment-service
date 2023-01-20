odoo.define('pos_advanced.AddressPopup', function(require) {
'use strict';

const { useState } = owl.hooks;
const { isConnectionError } = require('point_of_sale.utils');
const { Gui } = require('point_of_sale.Gui');
const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
var core = require('web.core');

var _t = core._t;

class AddressPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.partner = this.props.partner;
        this.address = this.props.address;
        this.state = useState({
            id: this.address && this.address.id || false,
            parent_id: this.partner && this.partner.id || false,
            type: this.address && this.address.type || 'delivery',
            name: this.address && this.address.name || '',
            street: this.address && this.address.street || '',
            city: this.address && this.address.city || '',
            zip: this.address && this.address.zip || '',
            state_id: this.address && this.address.state_id && this.address.state_id[0] || 0,
            country_id: this.address && this.address.country_id && this.address.country_id[0] || 0,
            email: this.address && this.address.email || '',
            phone: this.address && this.address.phone || '',
            mobile: this.address && this.address.mobile || '',
            comment: this.address && this.address.comment && $('<div>' + this.address.comment + '</div>').text() || '',
        });
    }

    selectType(ev) {
        const $radio = $(ev.target).closest('div.address-radio');
        const $input = $radio.find('input');
        $input.prop('checked', true);
        this.state.type = $input.val();
    }

    async setAddress(ev) {
        const $button = $(ev.target).closest('div.button');
        const $icon = $button.find('i');
        $button.addClass('disabled');
        $icon.toggleClass(['fa-edit', 'fa-circle-o-notch', 'fa-spin']);

        try {
            const values = {...this.state}
            values.state_id = values.state_id && parseInt(values.state_id) || false;
            values.country_id = values.country_id && parseInt(values.country_id) || false;
            await this.rpc({
                model: 'res.partner',
                method: 'create_from_ui',
                args: [values],
            });
            await this.rpc({
                model: 'res.partner',
                method: 'create_from_ui',
                args: [{id: values.parent_id}],
            });
            await this.env.pos.load_new_partners();
            this.trigger('close-popup');
        } catch (error) {
            if (isConnectionError(error)) {
                await Gui.showPopup('OfflineErrorPopup', {
                    title: this.env._t('Offline'),
                    body: this.env._t('Unable to save changes.'),
                });
            } else {
                throw error;
            }
        }
        $button.removeClass('disabled');
        $icon.toggleClass(['fa-edit', 'fa-circle-o-notch', 'fa-spin']);
    }
}

AddressPopup.template = 'AddressPopup';
AddressPopup.defaultProps = {
    title: _t('Address Information'),
};

Registries.Component.add(AddressPopup);

return AddressPopup;
});
