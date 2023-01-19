/** @odoo-module **/

import ClientDetailsEdit from 'point_of_sale.ClientDetailsEdit';
import Registries from 'point_of_sale.Registries';
import { Gui } from 'point_of_sale.Gui';

export const PosClientDetailsEdit = (ClientDetailsEdit) => 
    class PosClientDetailsEdit extends ClientDetailsEdit {

        getChild() {
            const partners = this.env.pos.partners;
            const childs = this.props.partner.child_ids;
            return partners.filter(partner => childs.includes(partner.id));
        }

        async setChild(id=0) {
            const partners = this.env.pos.partners;
            const child = id ? partners.filter(partner => partner.id === id) : undefined;
            await Gui.showPopup('AddressPopup', {
                partner: this.props.partner,
                child: child ? child[0] : undefined,
            });
        }

    };

Registries.Component.extend(ClientDetailsEdit, PosClientDetailsEdit)
