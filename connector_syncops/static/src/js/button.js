odoo.define('connector_syncops.SyncButton', function (require) {
"use strict";

const ListController = require('web.ListController');
const core = require('web.core');

const qweb = core.qweb;

const SyncButton = ListController.extend({
    events: _.extend({
        'click .o_button_sync': '_onClickSync',
    }, ListController.prototype.events),

    init: function () {
        this._super.apply(this, arguments);
        this.show_button = true;
    },

    renderButtons: function () {
        this._super.apply(this, arguments);
        if (this.show_button) {
            const $buttons = $(qweb.render('connector_syncops.sync_button'));
            this.$buttons.find('.o_list_export_xlsx').before($buttons);
        }
    },

    _onClickSync: function () {
        return this.do_action('connector_syncops.action_sync', {
            on_close: this.reload.bind(this, {}),
            additional_context: {
                ...this.controlPanelProps.action.context,
                active_model: this.controlPanelProps.action.res_model,
            },
        });
    }
});

return SyncButton;
});
    