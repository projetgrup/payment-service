/** @odoo-module alias=paylox.system.page **/
'use strict';

import core from 'web.core';
import rpc from 'web.rpc';
import publicWidget from 'web.public.widget';
import dialog from 'web.Dialog';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';
import { format } from 'paylox.tools';

const _t = core._t;

payloxPage.include({
    init: function (parent, options) {
        this._super(parent, options);
        this.system = new fields.string({
            default: false,
        });
    },

    _getParams: function () {
        const params = this._super.apply(this, arguments);
        const $items = $('input[type="checkbox"].payment-items:checked');
        if ($items.length) {
            const payment_ids = [];
            $items.each(function () { payment_ids.push(parseInt($(this).data('id'))); });
            params['system'] = this.system.value;
            params['payments'] = payment_ids;
        }
        return params;
    },

    _checkData: function () {
        var $items = $('input[type="checkbox"].payment-items');
        if (!$items.length) {
            return this._super.apply(this, arguments);
        }

        var $items = $('input[type="checkbox"].payment-items:checked');
        if (!$items.length) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please select at least one payment'),
            });
            this._enableButton();
            return false;
        } else {
            return this._super.apply(this, arguments);
        }
    },

});

publicWidget.registry.payloxSystemPage = publicWidget.Widget.extend({
    selector: '.payment-system',
    
    init: function (parent, options) {
        this._super(parent, options);
        this.currency = {
            id: 0,
            decimal: 2,
            name: '',
            separator: '.',
            thousand: ',', 
            position: 'after',
            symbol: '', 
        },
        this.amount = new fields.float({
            default: 0,
        });
        this.payment = {
            privacy: new fields.element({
                events: [['click', this._onClickPrivacy]],
            }),
            agreement: new fields.element({
                events: [['click', this._onClickAgreement]],
            }),
            membership: new fields.element({
                events: [['click', this._onClickMembership]],
            }),
            contact: new fields.element({
                events: [['click', this._onClickContact]],
            }),
            item: new fields.element({
                events: [['change', this._onChangePaid]],
            }),
            items: new fields.element({
                events: [['change', this._onChangePaidAll]],
            }),
            tags: new fields.element({
                events: [['click', this._onClickTag]],
            }),
            pivot: new fields.element(),
        };
    },
 
    start: function () {
        const self = this;
        return this._super.apply(this, arguments).then(function () {
            payloxPage.prototype._setCurrency.apply(self);
            payloxPage.prototype._start.apply(self);
            if (self.payment.item.exist) {
                self._onChangePaid();
            }
        });
    },

    _onChangePaidAll: function (ev) {
        if (this.payment.items.checked) {
            this.payment.item.checked = true;
        } else {
            this.payment.item.checked = false;
        }
        this._onChangePaid();
    },

    _onClickTag: function (ev) {
        const $button = $(ev.currentTarget);
        const pid = $button.data('id');
        $button.toggleClass('btn-light');

        _.each(this.payment.item.$, function(item) {
            const $el = $(item);
            if ($el.data('type-id') === pid) {
                if ($button.hasClass('btn-light')) {
                    $el.prop('checked', false);
                    $el.closest('tr').addClass('d-none');
                } else {
                    $el.prop('checked', true);
                    $el.closest('tr').removeClass('d-none');
                }
            }
        });
        this._onChangePaid();
    },

    _onChangePaid: function (ev) {
        if (!this.amount.exist) {
            return;
        }

        if (ev) {
            const $input = $(ev.currentTarget);
            const id = $input.data('id');
            const checked = $input.prop('checked');
            $('input[type="checkbox"][data-id="' + id + '"].payment-items').prop('checked', checked);
        }

        const $total = $('p.payment-amount-total');
        const $items = $('input[type="checkbox"].payment-items:checked');
        this.payment.items.checked = !!$items.length;

        let amount = 0;
        $items.each(function() { amount += parseFloat($(this).data('amount'))});
        
        const event = new Event('update');
        this.amount.value = format.float(amount);
        this.amount.$[0].dispatchEvent(event);

        $total.html(format.currency(amount, this.currency.position, this.currency.symbol, this.currency.decimal));
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
                title: _t('Contact Information'),
                $content: $('<div/>').html(content),
            }).open();
        });
    },
});

publicWidget.registry.payloxSystemPage = publicWidget.Widget.extend({
    selector: '.payment-dynamic',
    
    init: function (parent, options) {
        this._super(parent, options);
        this.currency = {
            id: 0,
            decimal: 2,
            name: '',
            separator: '.',
            thousand: ',', 
            position: 'after',
            symbol: '', 
        };
        this.amount = new fields.float({
            default: 0,
        });
        this.card = {
            number: new fields.element(),
        };
        this.page = {
            loading: new fields.element(),
            welcome: new fields.element(),
            amount: new fields.element(),
            card: new fields.element(),
            installment: new fields.element(),
            /*section: {
                all: new fields.element(),
                amount: new fields.element(),
                card: new fields.element(),
                installment: new fields.element(),
            },*/
        };

        this.button = {
            welcome: {
                done: new fields.element({
                    events: [['click', this._onClickWelcomeNext]],
                }),
            },
            amount: {
                prev: new fields.element({
                    events: [['click', this._onClickAmountPrev]],
                }),
                next: new fields.element({
                    events: [['click', this._onClickAmountNext]],
                }),
                done: new fields.element({
                    events: [['click', this._onClickAmountNext]],
                }),
            },
            card: {
                prev: new fields.element({
                    events: [['click', this._onClickCardPrev]],
                }),
                next: new fields.element({
                    events: [['click', this._onClickCardNext]],
                }),
                done: new fields.element({
                    events: [['click', this._onClickCardNext]],
                }),
            },
            installment: {
                prev: new fields.element({
                    events: [['click', this._onClickInstallmentPrev]],
                }),
                next: new fields.element({
                    events: [['click', this._onClickInstallmentNext]],
                }),
                done: new fields.element({
                    events: [['click', this._onClickInstallmentNext]],
                }),
            },
        };
    },
 
    start: function () {
        const self = this;
        return this._super.apply(this, arguments).then(function () {
            payloxPage.prototype._setCurrency.apply(self);
            payloxPage.prototype._start.apply(self);
            self.page.loading.$.removeClass('show');
            self.page.welcome.$.addClass('show');
            self.page.welcome.$.find('.invisible').addClass('show welcome-title');
            setTimeout(function() {
                self.page.welcome.$.find('.fade').addClass('show');
            }, 1500);
            console.log(self);
        });
    },

    _onClickWelcomeNext: function () {
        const self = this;
        this.page.welcome.$.addClass('slide').removeClass('show');
        setTimeout(function() {
            self.page.welcome.$.addClass('invisible');
            /*self.page.section.all.$.addClass('show');
            self.page.section.amount.$.addClass('active');*/
            self.page.amount.$.addClass('slide show').removeClass('invisible');
        }, 500);
    },

    _onClickAmountPrev: function () {
        const self = this;
        this.page.amount.$.removeClass('slide show');
        /*this.page.section.all.$.removeClass('show');
        this.page.section.amount.$.removeClass('active');*/
        setTimeout(function() {
            self.page.amount.$.addClass('invisible');
            self.page.welcome.$.removeClass('slide invisible').addClass('show');
        }, 500);
    },

    _onClickAmountNext: function () {
        const self = this;
        this.page.amount.$.addClass('slide').removeClass('show');
        setTimeout(function() {
            /*self.page.section.amount.$.find('.small').text(format.currency(self.amount.value || 0, self.currency.position, self.currency.symbol, self.currency.decimal));
            self.page.section.amount.$.addClass('done');
            self.page.section.card.$.addClass('active');*/
            self.page.amount.$.addClass('invisible');
            self.page.card.$.addClass('slide show').removeClass('invisible');
        }, 500);
    },

    _onClickCardPrev: function () {
        const self = this;
        self.page.card.$.removeClass('slide show');
        setTimeout(function() {
            /*self.page.section.card.$.removeClass('active');
            self.page.section.amount.$.removeClass('done');*/
            self.page.amount.$.removeClass('invisible slide').addClass('show');
            self.page.card.$.addClass('invisible');
        }, 500);
    },

    _onClickCardNext: function () {
        const self = this;
        this.page.card.$.addClass('slide').removeClass('show');
        setTimeout(function() {
            /*self.page.section.card.$.find('.small').text(self.card.number.value || '**** **** **** ****');
            self.page.section.card.$.addClass('done');
            self.page.section.installment.$.addClass('active');*/
            self.page.card.$.addClass('invisible');
            self.page.installment.$.addClass('slide show').removeClass('invisible');
        }, 500);
    },

    _onClickInstallmentPrev: function () {
        const self = this;
        self.page.installment.$.removeClass('slide show');
        setTimeout(function() {
            /*self.page.section.installment.$.removeClass('active');
            self.page.section.card.$.removeClass('done');*/
            self.page.card.$.removeClass('invisible slide').addClass('show');
            self.page.installment.$.addClass('invisible');
        }, 500);
    },

    _onClickInstallmentNext: function () {
        const self = this;
        alert('test');
    },
});

export default publicWidget.registry.payloxSystemPage;