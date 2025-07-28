odoo.define('web_mobile_application.redirect', require => {
'use strict';

const publicWidget = require('web.public.widget');
const rpc = require('web.rpc');

publicWidget.registry.mobileRedirect = publicWidget.Widget.extend({
    selector: '.o_mobile_redirect',
    events: {
        'submit form' : '_onSubmit',
        'click .btn-redirect-url': '_onClick',
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            const $booting = this.$('.o_booting');
            const $redirecting = this.$('.o_redirecting');
            if ($redirecting.length) {
                $redirecting.removeClass('hide');

                const $timer = $redirecting.find('span[name=timer]');
                const $button = this.$('button.btn-redirect-url');
                let timer = setInterval(() => {
                    $booting.addClass('hide');
                    let time = Number($timer.text());
                    if (time < 1) {
                        $button.click();
                        clearInterval(timer);
                    } else {
                        $timer.text(time - 1);
                    }
                }, 1000);

                const $cancel = this.$('button.btn-redirect-cancel');
                $cancel.click(() => {
                    $redirecting.addClass('hide');
                    clearInterval(timer);
                })
            } else {
                $booting.addClass('hide');
            }
        });
    },

    _onClick: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const $form = this.$('form');
        const $button = $(ev.currentTarget);
        const $loading = this.$('.o_loading');
        const $token = $form.find('input#token');

        if (ev.target.tagName === 'EM') {
            $loading.removeClass('hide');
            rpc.query({
                route: "/m/redirect/remove",
                params: {
                    url: $button.data('value'),
                    token: $token.val(),
                },
            }).then((res) => {
                if (res) {
                    $button.remove();
                } else {
                    this.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: _t('An error occured. Please try again.'),
                    });
                }
            }).guardedCatch(() => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please try again.'),
                });
            }).finally(() => {
                $loading.addClass('hide');
            });
        } else {
            $loading.removeClass('hide');
            window.location.href = `https://${$button.data('value')}/web?firebase_token=${$token.val()}`;
        }
    },

    _onSubmit: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const $form = $(ev.currentTarget);
        const $url = $form.find('input#url');
        const $loading = this.$('.o_loading');
        const $token = $form.find('input#token');

        $loading.removeClass('hide');
        rpc.query({
            route: "/m/redirect/save",
            params: {
                url: $url.val(),
                token: $token.val(),
            },
        }).then((res) => {
            if (res) {
                window.location.href = `https://${$url.val()}/web?firebase_token=${$token.val()}`;
            } else {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please try again.'),
                });
                $loading.addClass('hide');
            }
        }).guardedCatch(() => {
            this.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please try again.'),
            });
            $loading.addClass('hide');
        });
        return false;
    }
});
});
