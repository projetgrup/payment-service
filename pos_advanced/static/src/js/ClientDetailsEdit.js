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
            this.addresses = this.address ? [this.address] : ['delivery', 'invoice'];
            console.log(this.address);
            this.order = this.env.pos.get_order();
            this.state = useState({
                delivery: undefined,
                invoice: undefined,
            });
        }

        async willStart() {
            this.state.delivery = this.order.address.delivery;
            this.state.invoice = this.order.address.invoice;
        }

        getAddresses() {
            const addresses = [];
            const db = this.env.pos.db;
            const partner = db.get_partner_by_id(this.props.partner.id);
            const ids = partner && partner.child_ids || [];
            ids.forEach(function(id) {
                addresses.push(db.get_partner_by_id(id));
            });
            return addresses;
        }

        selectAddress(address)  {
            if (address.type === 'delivery') {
                this.state.delivery = this.state.delivery === address.id ? undefined : address.id;
            } else if (address.type === 'invoice') {
                this.state.invoice = this.state.invoice === address.id ? undefined : address.id;
            }
        }

        async setAddress(id=0) {
            const db = this.env.pos.db;
            const partner = this.props.partner;
            const address = id ? db.get_partner_by_id(id) : undefined;
            await Gui.showPopup('AddressPopup', {
                partner: partner,
                address: address,
                type: this.address,
            });
        }

    };

Registries.Component.extend(ClientDetailsEdit, PosClientDetailsEdit);
