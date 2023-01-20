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
            this.contact = this.props.contact;
            this.state = useState({
                contacts: [],
            });
        }

        getContacts() {
            const contacts = [];
            const db = this.env.pos.db;
            const partner = db.get_partner_by_id(this.props.partner.id);
            const ids = partner.child_ids;
            ids.forEach(function(id) {
                contacts.push(db.get_partner_by_id(id));
            });
            return contacts;
        }

        selectContact(id=0)  {
            if (this.state.contacts.includes(id)) {
                this.state.contacts = this.state.contacts.filter(cid => cid !== id);
            } else {
                this.state.contacts.push(id);
            }
        }

        async setContact(id=0) {
            const db = this.env.pos.db;
            const partner = this.props.partner;
            const contact = id ? db.get_partner_by_id(id) : undefined;
            await Gui.showPopup('AddressPopup', {
                partner: partner,
                contact: contact,
            });
        }

    };

Registries.Component.extend(ClientDetailsEdit, PosClientDetailsEdit);
