/** @odoo-module alias=paylox.system.page **/
'use strict';

import core from 'web.core';
import rpc from 'web.rpc';
import publicWidget from 'web.public.widget';
import dialog from 'web.Dialog';
import utils from 'web.utils';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';
import framework from 'paylox.framework';
import { format } from 'paylox.tools';

const _t = core._t;
const qweb = core.qweb;

payloxPage.include({
    init: function (parent, options) {
        this._super(parent, options);
        this.system = new fields.string({
            default: false,
        });
    },

    _getParams: function () {
        const params = this._super.apply(this, arguments);
        const $items = $('input.input-switch:checked');
        if ($items.length) {
            const payments = [];
            const items = [];
            $items.each(function () {
                const $this = $(this);
                const id = parseInt($this.data('id'));
                const amount = parseFloat($this.data('paid'));
                payments.push(id);
                items.push([id, amount]);
            });
            params['system'] = this.system.value;
            params['payments'] = payments;
            params['items'] = items;
        }
        return params;
    },

    _checkData: function () {
        var $items = $('input.input-switch');
        if (!$items.length) {
            return this._super.apply(this, arguments);
        }

        var $items = $('input.input-switch:checked');
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
    jsLibs: ['/payment_jetcheckout/static/src/lib/imask.js'],
    xmlDependencies: ['/payment_jetcheckout_system/static/src/xml/system.xml'],

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
        this.amountEditable = false;
        this.itemPriority = false;
        this.amount = new fields.float({
            default: 0,
        });
        this.vat = new fields.string();
        this.campaign = {
            name: new fields.string(),
        };
        this.payment = {
            amount: new fields.float({
                events: [
                    ['input', this._onInputAmount],
                    ['update', this._onUpdateAmount],
                ],
                mask: payloxPage.prototype._maskAmount.bind(this),
                default: 0,
            }),
            company: new fields.element({
                events: [['click', this._onClickCompany]],
            }),
            tag: new fields.element({
                events: [['click', this._onClickTag]],
            }),
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
            itemsBtn: new fields.element({
                events: [['click', this._onChangePaidAllBtn]],
            }),
            tags: new fields.element({
                events: [['click', this._onClickTags]],
            }),
            link: new fields.element({
                events: [['click', this._onClickLink]],
            }),
            pivot: new fields.element(),
            priority: new fields.element(),
            due: {
                date: new fields.element(),
                days: new fields.element(),
                payment: new fields.element(),
                warning: new fields.element(),
            },
            advance: {
                amount: 0,
                add: new fields.element({
                    events: [['click', this._onClickAdvanceAdd]],
                }),
                remove: new fields.element({
                    events: [['click', this._onClickAdvanceRemove]],
                }),
            }
        };
    },
 
    start: function () {
        const self = this;
        return this._super.apply(this, arguments).then(function () {
            payloxPage.prototype._setCurrency.apply(self);
            payloxPage.prototype._start.apply(self);
            if (self.payment.item.exist) {
                self.itemPriority = self.payment.priority.exist;
                self.amountEditable = self.payment.amount.exist;
                self._onChangePaid();
            }
        });
    },

    _onInputAmount: function () {
        const currency = this.currency;
        const inputs = $('input.input-switch');
        let amount = this.payment.amount.value;
        inputs.each(function () {
            const input = $(this);
            const paid = input.closest('tr').find('.payment-amount-paid');
            const residual = parseFloat(input.data('amount'));
            if (amount < 0) {
                amount = 0;
            }

            const value = residual > amount ? amount : residual;
            if (amount > 0) {
                paid.html(format.currency(value, currency.position, currency.symbol, currency.decimal));
                input.prop('checked', true);
                input.data('paid', value);
                amount -= residual;
            } else {
                paid.html(format.currency(0, currency.position, currency.symbol, currency.decimal));
                input.prop('checked', false);
                input.data('paid', 0);
            }
        });
        this._onChangePaid({
            allTarget: true,
        });
        //const amounts = inputs.map(function() { return parseFloat($(this).data('amount')); }).get();
    },

    _onUpdateAmount: function () {
        this.payment.amount._.updateValue();
    },

    _applyPriority: function () {
        if (this.itemPriority) {
            const items = this.payment.item.$;
            items.parent().addClass('disabled');

            const checks = items.filter(function() {
                const $this = $(this);
                return $this.hasClass('input-switch') && $this.is(':checked');
            });
            const last = checks.last();

            const unchecks = items.filter(function() {
                const $this = $(this);
                return $this.hasClass('input-switch') && !$this.is(':checked');
            });
            const first = unchecks.first();

            $('input[type="checkbox"][data-id="' + parseInt(last.data('id')) + '"].payment-items').parent().removeClass('disabled');
            $('input[type="checkbox"][data-id="' + parseInt(first.data('id')) + '"].payment-items').parent().removeClass('disabled');
        }
    },

    _onChangePaidAllBtn: function (ev) {
        const $input = $(ev.currentTarget).find('input');
        $input.prop('checked', !$input.prop('checked'));
        $input.trigger('change');
    },

    _onChangePaidAll: function (ev) {
        const checked = $(ev.currentTarget).is(':checked');
        this.payment.items.checked = checked;
        this.payment.item.checked = checked;
        this._onChangePaid(ev);
    },

    _onChangePaid: function (ev) {
        if (!this.amount.exist) {
            return;
        }

        const currency = this.currency;
        if (ev && ev.currentTarget) {
            const $input = $(ev.currentTarget);
            const id = parseInt($input.data('id'));
            const checked = $input.prop('checked');

            const $inputs = $('input[type="checkbox"][data-id="' + id + '"].payment-items');
            $inputs.each(function () { $(this).prop('checked', checked); });

            const $switches = $('input[type="checkbox"].payment-items.input-switch');
            $switches.each(function () {
                const $this = $(this);
                $this.data('paid', $this.is(':checked') ? parseFloat($this.data('amount')) : 0);
                const $paid = $this.closest('tr').find('.payment-amount-paid');
                $paid.html(format.currency(parseFloat($this.data('paid')), currency.position, currency.symbol, currency.decimal));
            });
        } else if (ev && ev.allTarget) {
            const $inputs = $('input.input-switch');
            $inputs.each(function () {
                const $input = $(this);
                const id = parseInt($input.data('id'));
                const checked = $input.prop('checked');
                $('input[type="checkbox"][data-id="' + id + '"].payment-items').prop('checked', checked);
            });
        }

        const $total = $('div.payment-amount-total');
        const $items = $('input.input-switch:checked');
        this.payment.items.checked = !!$items.length;

        if (this.payment.due.days.exist) {
            const self = this;
            const items = $items.map(function() {
                const $this = $(this);
                return [[parseInt($this.data('id')), parseFloat($this.data('paid'))]];
            }).get();
            rpc.query({
                route: '/p/due',
                params: { items }
            }).then(function (result) {
                if (result.advance_amount) {
                    self.payment.advance.add.html = _.str.sprintf(
                        _t('Click here for getting <span class="text-primary">%s</span> campaign by adding <span class="text-primary">%s</span> advance payment'),
                        result.advance_campaign,
                        format.currency(result.advance_amount, currency.position, currency.symbol, currency.decimal)
                    );
                    self.payment.advance.amount = result.advance_amount;
                } else {
                    self.payment.advance.add.html = '';
                    self.payment.advance.amount = 0;
                }
                self.payment.due.date.html = result.date;
                self.payment.due.days.html = result.days;
                self.campaign.name.value = result.campaign;
                self.campaign.name.$.trigger('change', [{ locked: true }]);
                if (result.hide_payment) {
                    self.payment.due.warning.$.removeClass('d-none');
                    self.payment.due.warning.$.find('p').text(result.hide_payment_message);
                    self.payment.due.payment.$.addClass('d-none');
                } else {
                    self.payment.due.warning.$.addClass('d-none');
                    self.payment.due.warning.$.find('p').text('');
                    self.payment.due.payment.$.removeClass('d-none');
                }
            });
        }

        this._applyPriority();
 
        let amount = 0;
        $items.each(function() { amount += parseFloat($(this).data('paid')); });

        const event = new Event('update');
        this.amount.value = format.float(amount);
        this.amount.$[0].dispatchEvent(event);

        if (this.amountEditable) {
            if (ev && ev.allTarget) {
                return;
            }
            this.payment.amount.value = format.float(amount, currency.decimal);
            this.payment.amount.$[0].dispatchEvent(event);
        } else {
            $total.html(format.currency(amount, currency.position, currency.symbol, currency.decimal));
        }
    },

    _onClickAdvanceAdd: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        framework.showLoading();
        const self = this;
        rpc.query({
            route: '/p/advance/add',
            params: { amount: this.payment.advance.amount }
        }).then(function () {
            window.location.reload();
        }).guardedCatch(function(error) {
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please try again.'),
                sticky: false,
            });
            framework.hideLoading();
        });
    },

    _onClickAdvanceRemove: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        framework.showLoading();
        const self = this;
        rpc.query({
            route: '/p/advance/remove',
            params: { pid: $(ev.currentTarget).data('id') }
        }).then(function () {
            window.location.reload();
        }).guardedCatch(function(error) {
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please try again.'),
                sticky: false,
            });
            framework.hideLoading();
        });
    },

    _onClickCompany: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const $button = $(ev.currentTarget);
        const cid = $button.data('id');
        rpc.query({route: '/p/company', params: { cid }}).then(function (token) {
            if (token) {
                framework.showLoading();
                window.location.assign('/p/' + token);
            }
        });
    },

    _onClickTag: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const $button = $(ev.currentTarget);
        const tid = $button.data('id');
        rpc.query({route: '/p/tag', params: { tid }}).then(function (token) {
            if (token) {
                framework.showLoading();
                window.location.assign('/p/' + token);
            }

        });
    },

    _onClickTags: function (ev) {
        const $button = $(ev.currentTarget);
        const pid = parseInt($button.data('id'));
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

    _onClickLink: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const amount = parseFloat(this.amount.$.data('value') || 0);
        const params = [
            ['amount', amount],
            ['currency', this.currency.name],
            ['vat', this.vat.value],
        ];

        let link = window.location.href;
        for (let i=0; i<params.length; i++) {
            if (!i) {
                link += '?';
            } else {
                link += '&';
            }
            link += params[i][0] + '=' + params[i][1];
        }
        navigator.clipboard.writeText(link);

        const content = qweb.render('paylox.system.link', { link });
        this.displayNotification({
            type: 'info',
            title: _t('Payment link is ready'),
            message: utils.Markup(content),
            sticky: true,
        });
    },
});

export default publicWidget.registry.payloxSystemPage;
