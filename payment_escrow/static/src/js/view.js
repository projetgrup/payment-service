odoo.define('payment_escrow.SyncButtonsController', function (require) {
'use strict';

const ListController = require('web.ListController');
const viewRegistry = require('web.view_registry');
const ListView = require('web.ListView');
const core = require('web.core');
const { qweb } = require('web.core');
const _t = core._t;

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
                message: _t('Please select at least one record to sync.'),
                type: 'warning'
            });
            return;
        }
        
        try {
            const result = await this._rpc({
                model: 'escrow.brand.sync.line',
                method: 'action_sync_brand_async',
                args: [selectedIds],
                context: this.getSession().user_context,
            });
            
            if (result.success) {
                this.do_action({'type': 'ir.actions.act_window_close'});
            } else {
                this.displayNotification({
                    title: _t('Sync Failed'),
                    message: result.message || _t('Sync failed to start'),
                    type: 'danger',
                });
                this._enableButtons();
            }
        } catch (error) {
            this.displayNotification({
                message: _t('Sync failed: ') + (error.message || error.data?.message || 'Unknown error'),
                type: 'danger'
            });
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