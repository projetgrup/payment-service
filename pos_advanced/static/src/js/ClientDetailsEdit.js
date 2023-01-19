/** @odoo-module **/

import ClientDetailsEdit from 'point_of_sale.ClientDetailsEdit';
import Registries from 'point_of_sale.Registries';
import { Gui } from 'point_of_sale.Gui';

export const PosClientDetailsEdit = (ClientDetailsEdit) => 
    class PosClientDetailsEdit extends ClientDetailsEdit {

        getChild() {
            const childs = this.props.partner.child_ids;
            return this.env.pos.partners.filter(partner => childs.includes(partner.id));
        }

        async addChild() {
            await Gui.showPopup('AddressPopup', {
                partner: this.props.partner,
            });
        }

    };

Registries.Component.extend(ClientDetailsEdit, PosClientDetailsEdit)
