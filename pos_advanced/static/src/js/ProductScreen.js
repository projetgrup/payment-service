/** @odoo-module **/

const { useListener } = require('web.custom_hooks');
import ProductScreen from 'point_of_sale.ProductScreen';
import Registries from 'point_of_sale.Registries';

export const PosProductScreen = (ProductScreen) => 
    class PosProductScreen extends ProductScreen {
        constructor() {
            super(...arguments);
            useListener('click-address', this._onClickAddress);
        }

        async _onClickAddress() {
            if (!this.currentOrder.get_client()) {
                return;
            }
            const { confirmed, payload: client } = await this.showTempScreen('AddressScreen', {
                client: this.currentOrder.get_client(),
                addressType: 'delivery',
            });
            if (confirmed) {
                this.currentOrder.set_client(client);
            }
        }
    };

Registries.Component.extend(ProductScreen, PosProductScreen);
