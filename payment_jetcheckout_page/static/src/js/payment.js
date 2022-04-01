odoo.define('payment_jetcheckout_page.payment_page', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var publicWidget = require('web.public.widget');
var Dialog = require('web.Dialog');

var _t = core._t;

publicWidget.registry.JetcheckoutPaymentPageOptions = publicWidget.Widget.extend({
    selector: '.payment-options',
    events: {
        'click div.payment-option': '_onClickPaymentOption',
    },

    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self._onToggleLoading();
        });
    },

    _onClickPaymentOption: function (ev) {
        this._onToggleLoading(true);
        const method = $(ev.currentTarget).find('input').val();
        window.location.assign('/payment/' + method);
    },

    _onToggleLoading: function (show=false) {
        const payment_pay = $('.payment_pay');
        const loading = $('.o_payment_loading');
        if (show) {
            payment_pay.addClass('disabled');
            payment_pay.prop('disabled', 'disabled');
            loading.css('opacity', 1).css('visibility', 'visible');
        } else {
            payment_pay.removeClass('disabled');
            payment_pay.prop('disabled', false);
            loading.css('opacity', 0).css('visibility', 'hidden');
        }
    },
});

publicWidget.registry.JetcheckoutPaymentPageBank = publicWidget.Widget.extend({
    selector: '.payment-bank',
    events: {
        'click button': '_onClickButton',
    },

    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self._onToggleLoading();
        });
    },

    _onClickButton: function (ev) {
        var self = this;
        new Dialog(self, {
            size: 'medium',
            title: _t('İşlemi onaylıyor musunuz?'),
            technical: false,
            buttons: [
                {text: _t("Onayla"), classes: 'btn-primary btn-validate'},
                {text: _t("İptal"), close: true},
            ],
            $content: $('<div/>', {
                html: 'Onayınız ile birlikte siparişiniz oluşturulacak.',
            }),
        }).open().opened(function () {
            const $button = $('.modal-footer .btn-validate');
            $button.click(function() {
                self._onValidateForm();
            });
        });
    },

    _onValidateForm: function () {
        var self = this;
        this._onToggleLoading(true);
        this._rpc({
            route: '/payment/bank/validate',
        }).then(function (url) {
            if (!url) {
                window.location.reload();
            } else {
                window.location.assign(url);
            }
        }).guardedCatch(function (error) {
            self._onToggleLoading();
            new Dialog(self, {
                size: 'medium',
                title: _t('Hata'),
                technical: false,
                buttons: [
                    {text: _t("Tamam"), classes: 'btn-primary', close: true},
                ],
                $content: $('<div/>', {
                    html: 'Bir hata meydana geldi. Lütfen tekrar deneyiniz.',
                }),
            }).open();
            if (config.isDebug()) {
                console.error(error);
            }
            self._onToggleLoading();
        });
    },

    _onToggleLoading: function (show=false) {
        const button = $('button');
        const loading = $('.o_payment_loading');
        if (show) {
            button.addClass('disabled');
            button.prop('disabled', 'disabled');
            loading.css('opacity', 1).css('visibility', 'visible');
        } else {
            button.removeClass('disabled');
            button.prop('disabled', false);
            loading.css('opacity', 0).css('visibility', 'hidden');
        }
    },
});

});
