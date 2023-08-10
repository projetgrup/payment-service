odoo.define('payment_syncops.SyncController', function (require) {
"use strict";

const PartnerController = require('payment_jetcheckout_system.PartnerController');
const ItemController = require('payment_jetcheckout_system.ItemController');
const SyncController = require('connector_syncops.SyncController');

SyncController.include({
    willStart: function() {
        const self = this;

        const shown = this._rpc({
            model: 'syncops.connector',
            method: 'count',
            args: ['payment_get_partner_list'],
        }).then(function (show) {
            self.show_button = !!show && self.show_button;
        }).guardedCatch(function (error) {
            console.error(error);
        });

        const granted = this.getSession().user_has_group('payment_jetcheckout_system.group_system_manager').then(function (has_group) {
            self.show_button = has_group && self.show_button;
        });

        return Promise.all([this._super.apply(this, arguments), shown, granted]);
    },
});

PartnerController.include(SyncController.prototype);
ItemController.include(SyncController.prototype);

});
