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
            const currentClient = this.currentOrder.get_client();
            const { confirmed, payload: address } = await this.showTempScreen('ClientListScreen', {
                client: currentClient,
                address: 'delivery',
            });
            if (confirmed) {
                this.currentOrder.set_address(address);
            }
        }
    };

Registries.Component.extend(ProductScreen, PosProductScreen);
