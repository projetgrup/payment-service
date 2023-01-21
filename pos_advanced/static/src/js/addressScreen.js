/** @odoo-module **/

const { useState } = owl.hooks;
import ClientListScreen from 'point_of_sale.ClientListScreen';
import Registries from 'point_of_sale.Registries';

export const PosClientListScreen = (ClientListScreen) => 
    class PosClientListScreen extends ClientListScreen {
        constructor() {
            super(...arguments);
            this.address = this.props.address;
        }

        willStart() {
            if (this.address) {
                this.state.editModeProps.address = 'delivery';
                console.log(this.state);
                this.editClient();
            }
        }

    };

Registries.Component.extend(ClientListScreen, PosClientListScreen);
