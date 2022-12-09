odoo.define('payment_jetcheckout_system.payment_page', function (require) {
"use strict";

var core = require('web.core');
var publicWidget = require('web.public.widget');
var rpc = require('web.rpc');
var utils = require('web.utils');
var dialog = require('web.Dialog');
var paymentPage = publicWidget.registry.JetcheckoutPaymentPage;

var round_di = utils.round_decimals;
var _t = core._t;

paymentPage.include({
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.$system = document.getElementById('system');
        });
    },

    _getParams: function () {
        const payment_ids = [];
        const $payable_items = $('input[type="checkbox"].payment-items:checked');
        $payable_items.each(function() { payment_ids.push(parseInt($(this).prop('name'))); });
        const params = this._super.apply(this, arguments);
        params['system'] = this.$system && this.$system.value || false;
        params['payment_ids'] = payment_ids;
        return params
    },
});

publicWidget.registry.JetcheckoutPaymentSystemPage = publicWidget.Widget.extend({
    selector: '.payment-system',

    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.$currency = $('#currency');
            self.precision = parseInt(self.$currency.data('decimal')) || 2;
            self.$amount = $('#amount');
            self.$amount_installment = $('#amount_installment');
            self.$privacy = $('#privacy_policy');
            self.$agreement = $('#distant_sale_agreement');
            self.$membership = $('#membership_agreement');
            self.$contact = $('#contact');
            self.$privacy.on('click', self._onClickPrivacy.bind(self));
            self.$agreement.on('click', self._onClickAgreement.bind(self));
            self.$membership.on('click', self._onClickMembership.bind(self));
            self.$contact.on('click', self._onClickContact.bind(self));
        });
    },

    format_currency: function(value) {
        const l10n = core._t.database.parameters;
        const formatted = _.str.sprintf('%.' + this.precision + 'f', round_di(value, this.precision) || 0).split('.');
        formatted[0] = utils.insert_thousand_seps(formatted[0]);
        const amount = formatted.join(l10n.decimal_point);
        if (this.$currency.data('position') === 'after') {
            return amount + ' ' + this.$currency.data('symbol');
        } else {
            return this.$currency.data('symbol') + ' ' + amount;
        }
    },

    _onClickPrivacy: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/privacy'}).then(function (content) {
            new dialog(this, {
                title: _t('Privacy Policy'),
                $content: $('<div/>').html(content),
            }).open();
        });
    },

    _onClickAgreement: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/agreement'}).then(function (content) {
            new dialog(this, {
                title: _t('Distant Sale Agreement'),
                $content: $('<div/>').html(content),
            }).open();
        });
    },

    _onClickMembership: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/membership'}).then(function (content) {
            new dialog(this, {
                title: _t('Membership Agreement'),
                $content: $('<div/>').html(content),
            }).open();
        });
    },

    _onClickContact: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/contact'}).then(function (content) {
            new dialog(this, {
                title: _t('Contact'),
                $content: $('<div/>').html(content),
            }).open();
        });
    },
});

});