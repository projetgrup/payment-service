odoo.define('payment_syncops.SyncController', function (require) {
"use strict";

const PartnerController = require('payment_jetcheckout_system.PartnerController');
const ItemController = require('payment_jetcheckout_system.ItemController');
const SyncButton = require('connector_syncops.SyncButton');

SyncButton.include({
    willStart: function() {
        const shown = this._rpc({
            model: 'syncops.connector',
            method: 'count',
            args: ['payment_get_partner_list'],
        }).then((show) => {
            this.show_button = !!show && this.show_button;
        }).guardedCatch((error) => {
            console.error(error);
        });

        const granted = this.getSession().user_has_group('payment_syncops.group_sync').then((has_group) => {
            this.show_button = has_group && this.show_button;
        });

        return Promise.all([this._super.apply(this, arguments), shown, granted]);
    },
});

PartnerController.include(SyncButton.prototype);
ItemController.include(SyncButton.prototype);
});
