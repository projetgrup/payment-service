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
            this.address = this.props.address;
            this.state = useState({
                address_id: undefined,
                invoice_id: undefined,
            });
        }

        async willStart() {
            this.state.address_id = this.partner.address_id;
            this.state.invoice_id = this.partner.invoice_id;
        }

        getAddresses() {
            const addresses = [];
            const db = this.env.pos.db;
            const partner = db.get_partner_by_id(this.props.partner.id);
            const ids = partner.child_ids;
            ids.forEach(function(id) {
                addresses.push(db.get_partner_by_id(id));
            });
            return addresses;
        }

        selectAddress(address)  {
            if (address.type === 'delivery') {
                this.state.address_id = this.state.address_id === address.id ? undefined : address.id;
            } else if (address.type === 'invoice') {
                this.state.invoice_id = this.state.invoice_id === address.id ? undefined : address.id;
            }

            this.partner.address_id = this.state.address_id;
            this.partner.invoice_id = this.state.invoice_id;
        }

        async setAddress(id=0) {
            const db = this.env.pos.db;
            const partner = this.props.partner;
            const address = id ? db.get_partner_by_id(id) : undefined;
            await Gui.showPopup('AddressPopup', {
                partner: partner,
                address: address,
            });
        }

    };

Registries.Component.extend(ClientDetailsEdit, PosClientDetailsEdit);
