/** @odoo-module **/

const { useState } = owl.hooks;
import { Gui } from 'point_of_sale.Gui';
import ClientListScreen from 'point_of_sale.ClientListScreen';
import Registries from 'point_of_sale.Registries';

export const PosClientListScreen = (ClientListScreen) => 
    class PosClientListScreen extends ClientListScreen {
        constructor() {
            super(...arguments);
            this._resetEditMode();
        }

        get clients() {
            let res;
            let query;
            let exist = false;
            let client = this.props.client;
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
            if (this.state.isNewClient) {
                this.clickNext();
            }
        }

        deactivateEditMode() {
            this.state.isEditMode = false;
            this._resetEditMode();
            this.render();
        }

        _resetEditMode() {
            const state = this.env.pos.config.partner_address_state_id || this.env.pos.company.state_id;
            const country = this.env.pos.config.partner_address_country_id || this.env.pos.company.country_id;
            this.state.editModeProps = {
                partner: {
                    state_id: state,
                    country_id: country,
                    country_code: this.env.pos.get_country_code(country[0]),
                },
            };
        }
    };

Registries.Component.extend(ClientListScreen, PosClientListScreen);
