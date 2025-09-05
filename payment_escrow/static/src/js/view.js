
odoo.define('payment_escrow.SyncButtonsController', function (require) {
'use strict';

const ListController = require('web.ListController');
const viewRegistry = require('web.view_registry');
const ListView = require('web.ListView');
const { qweb } = require('web.core');

const SyncButtonsController = ListController.extend({
    renderButtons: function ($node) {
        if ($node && $node[0] && $node[0]['nodeName'] === 'FOOTER') {
            const $buttons = $(qweb.render('payment_escrow.sync_buttons', {widget: this}));
            $buttons.on('click', '.o_list_button_sync', this._onSync.bind(this));
            $buttons.on('click', '.o_list_button_discard', this._onClose.bind(this));
            $buttons.appendTo($node);
            return;
        }
        return this._super.apply(this, arguments);
    },

    _onSync: async function () {
        this._disableButtons();
        
        const selectedIds = this.getSelectedIds();
        if (selectedIds.length === 0) {
            this._enableButtons();
            this.displayNotification({
                message: 'Please select at least one record to sync.',
                type: 'warning'
            });
            return;
        }
        
        try {
            const result = await this._rpc({
                model: 'escrow.brand.sync.line',
                method: 'action_sync_brand',
                args: [selectedIds],
                context: this.getSession().user_context,
            });
            
            if (result) {
                this.displayNotification({
                    message: 'Sync completed successfully!',
                    type: 'success'
                });
                this.do_action({'type': 'ir.actions.act_window_close'})
            }
        } catch (error) {
            this.displayNotification({
                message: 'Sync failed: ' + error.message,
                type: 'danger'
            });
            console.error('Sync error:', error);
        } finally {
            this._enableButtons();
        }
    },

    _onClose: function () {
        this.do_action({'type': 'ir.actions.act_window_close'})
    },
});

const SyncButtonsView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: SyncButtonsController,
    }),
});

viewRegistry.add('sync_buttons', SyncButtonsView);

return SyncButtonsController;
});