odoo.define('payment_syncops.SyncController', function (require) {
"use strict";

const PartnerController = require('payment_jetcheckout_system.PartnerController');
const ItemController = require('payment_jetcheckout_system.ItemController');
const SyncController = require('connector_syncops.SyncController');

SyncController.include({
    willStart: function() {
        const self = this;
        const granted = this.getSession().user_has_group('payment_jetcheckout_system.group_system_manager').then(function (has_group) {
            self.show_button = has_group && self.show_button;
        });
        return Promise.all([this._super.apply(this, arguments), granted]);
    },
});

PartnerController.include(SyncController.prototype);
ItemController.include(SyncController.prototype);

});
