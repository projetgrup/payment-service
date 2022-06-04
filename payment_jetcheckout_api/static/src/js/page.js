odoo.define('payment_jetcheckout_api.payment_page', function (require) {
"use strict";

var config = require('web.config');
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
        const method = $(ev.currentTarget).find('input').val();
        window.location.assign('/payment/' + method);
    },
});

publicWidget.registry.JetcheckoutPaymentApiBank = publicWidget.Widget.extend({
    selector: '.payment-bank',
    events: {
        'click button': '_onClickButton',
    },

    start: function () {
        return this._super.apply(this, arguments).then(function () {
            framework.hideLoading();
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
        framework.showLoading();
        this._rpc({
            route: '/payment/bank/validate',
        }).then(function (url) {
            if (!url) {
                window.location.reload();
            } else {
                window.location.assign(url);
            }
        }).guardedCatch(function (error) {
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
            framework.hideLoading();
        });
    },
});

});
