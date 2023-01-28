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
