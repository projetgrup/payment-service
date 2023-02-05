/** @odoo-module **/

import ClientListScreen from 'point_of_sale.ClientListScreen';
import Registries from 'point_of_sale.Registries';

export const PosClientListScreen = (ClientListScreen) => 
    class PosClientListScreen extends ClientListScreen {
        constructor() {
            super(...arguments);
            this.state = {
                ...this.state,
                currentClient: this.props.client,
            }
        }

        get clients() {
            let res;
            let query;
            let client = this.state.currentClient;
            if (this.state.query && this.state.query.trim() !== '') {
                query = true;
                res = this.env.pos.db.search_partner(this.state.query.trim());
            } else {
                query = false;
                res = this.env.pos.db.get_partners_sorted(1000);
            }

            let exist = false;
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
            this.state.currentClient = this.props.client ? this.env.pos.db.get_partner_by_id(this.props.client.id) : null;
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
