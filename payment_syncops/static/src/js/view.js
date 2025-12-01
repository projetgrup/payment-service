
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
            this._userCancelled = false;
            
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
                this._userCancelled = false;
            } else if (data.type === 'error') {
                this.showError(data.message || _t('Operation failed'));
                this._userCancelled = false;
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
            
            $widget.find('.o_sync_cancel').on('click', () => {
                this._userCancelled = true;
                const channel = `progress_${session.uid}_${session.db}`;
                this._rpc({
                    route: '/syncops/progress/cancel',
                    params: {
                        channel: channel,
                    },
                });
                this.destroyProgress();
            });

            $widget.find('.o_sync_toggle_errors').on('click', () => {
                $widget.find('.o_sync_errors').slideToggle();
            });

            $widget.appendTo($('body'));
            this._widget = $widget;
        },

        showError: function(message) {
            if (this._widget) {
                const $errors = this._widget.find('.o_sync_errors');
                const $list = $errors.find('ul');
                const $toggleBtn = this._widget.find('.o_sync_toggle_errors');
                const $countBadge = $toggleBtn.find('.o_error_count');

                $list.append($('<li>').text(message));
                
                // Update count
                let count = parseInt($countBadge.text()) || 0;
                count++;
                $countBadge.text(count);
                
                // Show toggle button
                $toggleBtn.show();
                
                this._widget.find('.progress-bar').removeClass('progress-bar-animated').addClass('bg-danger');
            } else {
                this._notify(message, 'danger');
            }
        },

        updateProgress: function(data) {
            if (this._userCancelled) {
                return;
            }
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
