/** @odoo-module **/

const { useState } = owl.hooks;
import { Gui } from 'point_of_sale.Gui';
import ClientDetailsEdit from 'point_of_sale.ClientDetailsEdit';
import Registries from 'point_of_sale.Registries';

export const PosClientDetailsEdit = (ClientDetailsEdit) => 
    class PosClientDetailsEdit extends ClientDetailsEdit {
        constructor() {
            super(...arguments);
            this.partner = this.props.partner;
            this.type = this.props.addressType;
            this.types = this.type ? [this.type] : ['delivery', 'invoice'];
            this.order = this.env.pos.get_order();
            this.state = useState({
                delivery: undefined,
                invoice: undefined,
                countryCode: this.env.pos.get_country_code(this.partner.country_id[0]),
            });
        }

        captureChange(event) {
            super.captureChange(...arguments);
            if (['country_id', 'vat'].includes(event.target.name)) {
                const vat = (this.changes.vat || this.partner.vat || '').replace(/[A-Za-z]/g, '');
                const countryCode = this.env.pos.get_country_code(parseInt(this.changes.country_id));
                this.state.countryCode = countryCode;
                this.changes.vat = countryCode + vat;
            }
        }

        getPartnerVat(vat) {
            return (vat || '').replace(/[A-Za-z]/g, '');
        }

        async willStart() {
            const self = this;
            const address = this.order.get_address();
            this.types.forEach(function(type) { self.state[type] = address[type] && address[type].id });
        }

        getAddresses() {
            const addresses = [];
            const db = this.env.pos.db;
            const partner = db.get_partner_by_id(this.partner.id);
            const ids = partner && partner.child_ids || [];
            ids.forEach(function(id) {
                addresses.push(db.get_partner_by_id(id));
            });
            return addresses;
        }

        selectAddress(address)  {
            const type = this.type;
            const id = this.state[type] === address.id ? undefined : address.id;
            this.state[type] = id;

            const result = {};
            result[type] = id ? address : this.partner;
            this.order.set_address({ ...result });
        }

        async saveAddress(address) {
            await Gui.showPopup('AddressPopup', {
                partner: this.partner,
                type: this.type,
                order: this.order,
                address: address,
            });
        }

    };

Registries.Component.extend(ClientDetailsEdit, PosClientDetailsEdit);
