odoo.define('payment_jetcheckout_api.payment_page', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var publicWidget = require('web.public.widget');
var Dialog = require('web.Dialog');
var framework = require('payment_jetcheckout.framework');
var paymentPage = publicWidget.registry.JetcheckoutPaymentPage;

var _t = core._t;

paymentPage.include({
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.$system = document.getElementById('system');
        });
    },

    _getParams: function () {
        const params = this._super.apply(this, arguments);
        params['api'] = this.$system && this.$system.value == 'api' || false;
        return params
    },
});

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
        'click button#validate': '_onValidateButton',
        'click button#submit': '_onSubmitButton',
    },

    start: function () {
        return this._super.apply(this, arguments).then(function () {
            framework.hideLoading();
        });
    },

    _onValidateButton: function (ev) {
        var self = this;
        let popup = new Dialog(self, {
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
        });
        popup.open().opened(function () {
            const $button = $('.modal-footer .btn-validate');
            $button.click(function() {
                framework.showLoading();
                window.location.assign('/payment/bank/success')
            });
        });
    },

    _onSubmitButton: function () {
        var self = this;
        framework.showLoading();
        this._rpc({
            route: '/payment/bank/validate',
        }).then(function (url) {
            window.location.assign(url);
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
