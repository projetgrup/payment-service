/** @odoo-module **/

import ClientListScreen from 'point_of_sale.ClientListScreen';
import Registries from 'point_of_sale.Registries';

export const PosClientListScreen = (ClientListScreen) => 
    class PosClientListScreen extends ClientListScreen {
        get clients() {
            let res;
            let query;
            let exist = false;

            let client = this.props.client;
            if (this.props.client) {
                client = this.env.pos.db.get_partner_by_id(this.props.client.id);
            }

            if (this.state.query && this.state.query.trim() !== '') {
                query = true;
                res = this.env.pos.db.search_partner(this.state.query.trim());
            } else {
                query = false;
                res = this.env.pos.db.get_partners_sorted(1000);
            }

            if (client) {
                let clientIndex = res.findIndex(c => c.id === client.id);
                if (clientIndex >= 0) {
                    exist = true;
                    client = res.splice(clientIndex, 1)[0];
                }
            }

            res = res.sort(function (a, b) { return (a.name || '').localeCompare(b.name || '') });
            if (client) {
                if (!query || exist) {
                    res.unshift(client);
                }
            }

            return res;
        }

        async saveChanges() {
            await super.saveChanges(...arguments);
            this._updateAddress();
            if (this.state.isNewClient) {
                this.clickNext();
            }
        }

        _updateAddress() {
            const values = {};
            const db = this.env.pos.db;
            const order = this.env.pos.get_order();
            const address = order.get_address();
            for (const [key, value] of Object.entries(address)) {
                if (key === 'id') continue;
                if (!value) continue;
                values[key] = db.get_partner_by_id(value.id);
            }
            order.set_address({ ...values });
        }
    };

Registries.Component.extend(ClientListScreen, PosClientListScreen);
