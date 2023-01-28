odoo.define('payment_jetcheckout_api.payment_page', function (require) {
"use strict";

var core = require('web.core');
var publicWidget = require('web.public.widget');
var Dialog = require('web.Dialog');
var framework = require('payment_jetcheckout.framework');

var _t = core._t;

publicWidget.registry.JetcheckoutPaymentApiOptions = publicWidget.Widget.extend({
    selector: '.payment-options',
    events: {
        'click div.payment-option': '_onClickPaymentOption',
    },

    start: function () {
        return this._super.apply(this, arguments).then(function () {
            framework.hideLoading();
        });
    },

    _onClickPaymentOption: function (ev) {
        framework.showLoading();
        const option = $(ev.currentTarget).attr('name');
        window.location.assign('/payment/' + option);
    },
});

publicWidget.registry.JetcheckoutPaymentApiCreditCard = publicWidget.Widget.extend({
    selector: '.payment-credit-card',

    start: function () {
        return this._super.apply(this, arguments).then(function () {
            framework.hideLoading();
        });
    },
});

publicWidget.registry.JetcheckoutPaymentApiBank = publicWidget.Widget.extend({
    selector: '.payment-bank',
    events: {
        'click button#confirm': '_onBankConfirmButton',
        'click button#return': '_onBankReturnButton',
    },

    start: function () {
        return this._super.apply(this, arguments).then(function () {
            framework.hideLoading();
        });
    },

    _onBankConfirmButton: function (ev) {
        var self = this;
        let popup = new Dialog(self, {
            size: 'medium',
            title: _t('Are you confirm the transaction?'),
            technical: false,
            buttons: [
                {text: _t("Confirm"), classes: 'btn-primary btn-confirm'},
                {text: _t("Cancel"), close: true},
            ],
            $content: $('<div/>', {
                html: _t('Transaction is going to be concluded after your confirmation'),
            }),
        });
        popup.open().opened(function () {
            const $button = $('.modal-footer .btn-confirm');
            $button.click(function() {
                framework.showLoading();
                self._rpc({
                    route: '/payment/bank/confirm',
                }).then(function (url) {
                    window.location.assign(url);
                }).guardedCatch(function (error) {
                    new Dialog(self, {
                        size: 'medium',
                        title: _t('Error'),
                        technical: false,
                        buttons: [
                            {text: _t("Okay"), classes: 'btn-primary', close: true},
                        ],
                        $content: $('<div/>', {
                            html: _t('An error occured. Please try again.'),
                        }),
                    }).open();
                    framework.hideLoading();
                });
            });
        });
    },

    _onBankReturnButton: function () {
        var self = this;
        framework.showLoading();
        this._rpc({
            route: '/payment/bank/return',
        }).then(function (url) {
            window.location.assign(url);
        }).guardedCatch(function (error) {
            new Dialog(self, {
                size: 'medium',
                title: _t('Error'),
                technical: false,
                buttons: [
                    {text: _t("Okay"), classes: 'btn-primary', close: true},
                ],
                $content: $('<div/>', {
                    html: _t('An error occured. Please try again.'),
                }),
            }).open();
            framework.hideLoading();
        });
    },
});

});
