
odoo.define('payment_syncops.ProgressService', function (require) {
    "use strict";

    const AbstractService = require('web.AbstractService');
    const core = require('web.core');
    const session = require('web.session');
    const { qweb } = require('web.core');
    const _t = core._t;

    const ProgressService = AbstractService.extend({
        dependencies: ['bus_service'],

        start: function () {
            this._super.apply(this, arguments);
            this._widget = null;
            
            const channel = `progress_${session.uid}_${session.db}`;
            
            this.call('bus_service', 'addChannel', channel);
            this.call('bus_service', 'onNotification', this, this._onBusNotification);
        },

        _onBusNotification: function (notifications) {
            for (const notif of notifications) {
                if (notif.type.indexOf('progress') !== -1) {
                    this._handleBusNotification(notif.payload);
                }
            }
        },

        _handleBusNotification: function(data) {
            if (data.type === 'progress') {
                this.updateProgress(data);
            } else if (data.type === 'complete') {
                this.updateProgress(data);
                this._notify(data.message || _t('Operation completed successfully!'), 'success');
            } else if (data.type === 'error') {
                this._notify(data.message || _t('Operation failed'), 'danger');
                this.destroyProgress();
            }
        },

        showProgress: function(total) {
            this.destroyProgress();
            
            const $widget = $(qweb.render('payment_syncops.SyncProgressWidget', {
                processed: 0,
                total: total,
                percent: 0,
                message: _t('Starting...'),
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
                setTimeout(() => {
                    this.destroyProgress();
                }, 2000);
            }
        },

        destroyProgress: function() {
            if (this._widget) {
                this._widget.remove();
                this._widget = null;
            }
        },

        _notify: function(message, type) {
            this.call('notification', 'notify', {
                message: message,
                type: type,
            });
        }
    });

    core.serviceRegistry.add('syncops_progress_service', ProgressService);
    return ProgressService;
});
