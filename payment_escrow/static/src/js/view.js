
odoo.define('payment_escrow.SyncButtonsController', function (require) {
'use strict';

const ListController = require('web.ListController');
const viewRegistry = require('web.view_registry');
const ListView = require('web.ListView');
const { qweb } = require('web.core');
const core = require('web.core');
const _t = core._t;

const SyncProgressManager = {
    _widget: null,
    _channel: null,

    showProgress: function(total) {
        this.destroyProgress();
        
        const $widget = $(qweb.render('payment_escrow.BrandSyncProgressWidget', {
            processed: 0,
            total: total,
            percent: 0,
            message: _t('Starting sync...'),
        }));
        
        $widget.css({
            'position': 'fixed',
            'bottom': '20px',
            'right': '20px',
            'z-index': '99999',
            'width': '350px',
            'display': 'block',
            'opacity': '1'
        });
        
        $widget.appendTo($('body'));
        this._widget = $widget;
    },

    updateProgress: function(data) {
        if (!this._widget || !this._widget.parent().length) {
            this.showProgress(data.total);
        }
        const percent = data.total > 0 ? Math.round((data.processed / data.total) * 100) : 0;
        
        const $bar = this._widget.find('.progress-bar');
        const $badge = this._widget.find('.badge');
        const $message = this._widget.find('.text-muted');
        
        $bar.css('width', percent + '%')
            .attr('aria-valuenow', percent)
            .text(percent + '%');
            
        $badge.text(data.processed + ' / ' + data.total);
        
        if (data.message) {
            $message.text(data.message);
        }

        if (data.processed >= data.total) {
            this.destroyProgress();
            this.stopBusListener();
        }
    },

    destroyProgress: function() {
        if (this._widget) {
            this._widget.remove();
            this._widget = null;
        }
    },

    startBusListener: function(channel, controller) {
        this.stopBusListener();
        this._channel = channel;
        if (controller) {
            controller.call('bus_service', 'addChannel', channel);
            controller.call('bus_service', 'onNotification', this, this._onBusNotification);
        }
    },

    stopBusListener: function() {
        this._channel = null;
    },

    _onBusNotification: function(notifications) {
        if (!this._channel) return;
        
        for (const notif of notifications) {
            if (notif.type === 'brand_sync_progress') {
                this._handleBusNotification(notif.payload);
            }
        }
    },

    _handleBusNotification: function(data) {
        if (data.type === 'progress') {
            this.updateProgress(data);
        } else if (data.type === 'complete') {
            this.updateProgress(data);
            this._notify(data.message || _t('Sync completed successfully!'), 'success');
        } else if (data.type === 'error') {
            this._notify(data.message || _t('Sync failed'), 'danger');
            this.destroyProgress();
            this.stopBusListener();
        }
    },

    _notify: function(message, type) {
        core.bus.trigger('display_notification', {
            message: message,
            type: type,
            sticky: false,
        });
    }
};

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
                SyncProgressManager.startBusListener(result.channel, this);
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