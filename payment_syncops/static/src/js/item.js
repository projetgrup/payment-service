odoo.define('payment_syncops.ItemController', function (require) {
"use strict";

const ItemController = require('payment_jetcheckout_system.ItemController');
const core = require('web.core');

const qweb = core.qweb;

ItemController.include({
    events: _.extend({
        'click .o_button_sync': '_onClickSync',
    }, ItemController.prototype.events),

    init: function () {
        this._super.apply(this, arguments);
        this.show_button = true;
    },

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

    renderButtons: function () {
        this._super.apply(this, arguments);
        if (this.show_button) {
            const $buttons = $(qweb.render('payment_syncops.item_button'));
            this.$buttons.find('.o_list_export_xlsx').before($buttons);
        }
    },

    _onClickSync: function () {
        return this.do_action('payment_syncops.action_sync', {
            on_close: this.reload.bind(this, {}),
            additional_context: {
                default_type: 'item',
                default_system: this.controlPanelProps.action.context.active_system,
            },
        });
    }
});

});
    