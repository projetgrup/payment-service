/** @odoo-module **/

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
            this.state = {
                childIds: [],
                selectedIds: {
                    delivery: undefined,
                    invoice: undefined,
                },
                countryCode: this.env.pos.get_country_code(this.partner.country_id[0]),
            };
        }

        captureChange(event) {
            super.captureChange(...arguments);
            if (['country_id', 'vat'].includes(event.target.name)) {
                const vat = (this.changes.vat || this.partner.vat || '').replace(/[A-Za-z]/g, '');
                const countryCode = this.env.pos.get_country_code(parseInt(this.changes.country_id));
                this.state.countryCode = countryCode;
                this.changes.vat = countryCode + vat;
                this.render();
            }
        }

        getPartnerVat(vat) {
            return (vat || '').replace(/[A-Za-z]/g, '');
        }

        async willStart() {
            const self = this;
            const address = this.order.get_address();
            this.types.forEach(function(type) { self.state.selectedIds[type] = address[type] && address[type].id });

            const childIds = [];
            const db = this.env.pos.db;
            const partner = db.get_partner_by_id(this.partner.id);
            const ids = partner && partner.child_ids || [];
            for (let i = 0; i < ids.length; i++) {
                const child = {...db.get_partner_by_id(ids[i])};
                child.sequence = i;
                childIds.push(child);
            }
            this.state.childIds = childIds;
        }

        selectAddress(address)  {
            const type = this.type;
            const id = this.state.selectedIds[type] === address.id ? undefined : address.id;
            this.state.selectedIds[type] = id;

            const result = {};
            result[type] = id ? address : this.partner;
            this.order.set_address({ ...result });
            this.render();
        }

        _preparePayload(child)  {
            return {
                type: child.type,
                name: child.name,
                street: child.street,
                city: child.city,
                zip: child.zip,
                email: child.email,
                phone: child.phone,
                mobile: child.mobile,
                comment: child.comment,
                state_id: child.state_id ? child.state_id[0] : false,
                country_id: child.country_id ? child.country_id[0] : false,
            }
        }

        async saveAddress(address) {
            const self = this;
            const childIds = this.state.childIds;
            const childLength = childIds.length;
            const { confirmed, payload } = await Gui.showPopup('AddressPopup', {
                partner: this.partner,
                type: this.type,
                order: this.order,
                address: address,
                sequence: childLength,
            });
            if (confirmed) {
                if (payload.sequence === childLength) {
                    this.state.childIds.push(payload);
                } else {
                    this.state.childIds[payload.sequence] = payload;
                }

                const changes = [];
                this.state.childIds.forEach(function(child) {
                    if (child.id) {
                        changes.push([1, child.id, self._preparePayload(child)]);
                    } else {
                        changes.push([0, 0, self._preparePayload(child)]);
                    }
                });
                this.changes['child_ids'] = changes;
            }
            this.render();
        }

    };

Registries.Component.extend(ClientDetailsEdit, PosClientDetailsEdit);
