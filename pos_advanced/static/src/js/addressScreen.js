/** @odoo-module **/

import ClientListScreen from 'point_of_sale.ClientListScreen';
import Registries from 'point_of_sale.Registries';
class AddressScreen extends ClientListScreen {
    constructor() {
        super(...arguments);
        this.addressType = this.props.addressType;
    }

    willStart() {
        this.editClient();
    }

    back() {
        this.props.resolve({ confirmed: false, payload: false });
        this.trigger('close-temp-screen');
    }

    async saveChanges(event) {
        try {
            let pid = await this.rpc({
                model: 'res.partner',
                method: 'create_from_ui',
                args: [event.detail.processedChanges],
            });
            await this.env.pos.load_new_partners();
            const client = this.env.pos.db.get_partner_by_id(pid);
            this.props.resolve({ confirmed: true, payload: client });
            this.trigger('close-temp-screen');
        } catch (error) {
            if (error.message.code < 0) {
                await this.showPopup('OfflineErrorPopup', {
                    title: this.env._t('Offline'),
                    body: this.env._t('Unable to save changes.'),
                });
            } else {
                throw error;
            }
        }
    }

};

AddressScreen.template = 'AddressScreen'
Registries.Component.add(AddressScreen);
