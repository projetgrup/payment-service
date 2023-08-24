/** @odoo-module alias=paylox.page **/
'use strict';

import config from 'web.config';
import core from 'web.core';
import rpc from 'web.rpc';
import publicWidget from 'web.public.widget';
import dialog from 'web.Dialog';
import cards from 'paylox.cards';
import framework from 'paylox.framework';
import fields from 'paylox.fields';
import { format } from 'paylox.tools';

const _t = core._t;
const qweb = core.qweb;

publicWidget.registry.payloxPage = publicWidget.Widget.extend({
    selector: '.payment-card',
    jsLibs: ['/payment_jetcheckout/static/src/lib/imask.js'],
    xmlDependencies: ['/payment_jetcheckout/static/src/xml/templates.xml'],


    init: function (parent, options) {
        this._super(parent, options);
        this.card = {
            number: new fields.string({
                events: [
                    ['focus', this._onFocusCardFront],
                    ['accept', this._onAcceptCardNumber],
                ],
                mask: {
                    mask: cards,
                    dispatch: function (appended, masked) {
                        const number = (masked.value + appended).replace(/\D/g, '');
                        for (const mask of masked.compiledMasks) {
                            const re = new RegExp(mask.regex);
                            if (number.match(re) != null) {
                                return mask;
                            }
                        }
                    }
                }
            }),
            date: new fields.string({
                events: [
                    ['focus', this._onFocusCardFront],
                    ['accept', this._onAcceptDate],
                ],
                mask: this._maskDate,
            }),
            code: new fields.string({
                events: [
                    ['focus', this._onFocusCardBack],
                    ['accept', this._onAcceptCode],
                ],
                mask: {
                    mask: '000[0]',
                }
            }),
            icon: new fields.string(),
            logo: new fields.string(),
            holder: new fields.string({
                events: [
                    ['input', this._onInputHolder],
                    ['focus', this._onFocusCardFront],
                ],
            }),
            sample: new fields.string({
                events: [['click', this._onClickCardSample]],
            }),
            preview: new fields.string(),
            type: '',
            family: '',
            bin: '',
        };
        this.campaign = {
            name: new fields.string(),
            table: new fields.string({
                events: [['click', this._onClickCampaingTable]],
            }),
        }
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
            events: [
                ['input', this._onInputAmount],
                ['update', this._onUpdateAmount],
                ['focus', this._onFocusCardFront],
            ],
            mask: this._maskAmount,
            default: 0,
        });
        this.installment = {
            table: new fields.string({
                events: [['click', this._onClickInstallmentTable]],
            }),
            row: new fields.string({
                events: [['click', this._onClickRow]],
            }),
            rowempty: new fields.string(),
            col: new fields.string(),
            colempty: new fields.string(),
        };
        this.terms = {
            ok: new fields.boolean(),
            all: new fields.string({
                events: [['click', this._onClickPaymentTerms]],
            }),
        };
        this.discount = {
            single: new fields.float({
                default: 0,
            }),
        };
        this.payment = {
            button: new fields.string({
                events: [['click', this._onClickPaymentButton]],
            }),
            form: new fields.string({
                events: [['click', this._onClickPaymentButton]],
            }),
            successurl: new fields.string(),
            failurl: new fields.string(),
            s2s: new fields.boolean({
                default: false,
            }),
            order: new fields.integer(),
            invoice: new fields.integer(),
            subscription: new fields.integer(),
        };
        this.partner = new fields.integer({
            default: 0,
        });
    },

    _setCurrency: function () {
        const currency = $('[field=currency]');
        if (!currency.length) {
            console.error('Currency field not found. Amount mask will not work.');
        }

        this.currency = {
            id: currency.data('id'),
            name: currency.data('name'),
            decimal: currency.data('decimal'),
            separator: currency.data('separator'),
            thousand: currency.data('thousand'),
            position: currency.data('position'),
            symbol: currency.data('symbol'),
        }
    },

    _updateCurrency: function ($currency) {
        if (!$currency) {
            $currency = $('[field=currency]');
        } else if ($currency instanceof HTMLElement) {
            $currency = $($currency);
        } else if (!($currency instanceof jQuery)) {
            console.error('Currency argument must be HTMLElement or jQuery object.');
            return;
        }

        const currency = $('[field=currency]');
        currency.data('id', $currency.data('id'));
        currency.data('name', $currency.data('name'));
        currency.data('decimal', $currency.data('decimal'));
        currency.data('separator', $currency.data('separator'));
        currency.data('thousand', $currency.data('thousand'));
        currency.data('position', $currency.data('position'));
        currency.data('symbol', $currency.data('symbol'));

        currency.attr('data-id', $currency.data('id'));
        currency.attr('data-name', $currency.data('name'));
        currency.attr('data-decimal', $currency.data('decimal'));
        currency.attr('data-separator', $currency.data('separator'));
        currency.attr('data-thousand', $currency.data('thousand'));
        currency.attr('data-position', $currency.data('position'));
        currency.attr('data-symbol', $currency.data('symbol'));

        currency.trigger('update');
    },

    _maskAmount: function () {
        return {
            mask: Number,
            min: 0,
            signed: false,
            padFractionalZeros: true,
            normalizeZeros: true,
            scale: this.currency.decimal,
            thousandsSeparator: this.currency.thousand,
            radix: this.currency.separator,
            scale: this.currency.decimal,
            mapToRadix: [this.currency.thousand],
        }
    },

    _maskDate: function () {
        return {
           mask: 'MM{/}YY',
           blocks: {
               YY: {
                   mask: IMask.MaskedRange,
                   from: 0,
                   to: 99
               },
               MM: {
                   mask: IMask.MaskedRange,
                   from: 1,
                   to: 12
               },
            }
        }
    },

    _start: function () {
        const t = this;
        $('[field]').each(function(_, e) {
            const name = e.getAttribute('field');
            const ids = name.split('.');
            if (!ids.length) {
                return;
            }

            try {
                let i = 0;
                let l = ids.length - 1;
                let s = t;

                while (i < l) {
                    const id = ids[i];
                    s = s[id];
                    i++;
                }

                s[ids[l]].$ = s[ids[l]].$.add(e);
                s[ids[l]].start(t, name);
            } catch {}
        });
    },
 
    start: function () {
        const self = this;
        return this._super.apply(this, arguments).then(function () {
            self._setCurrency();
            self._start();
            const $currency = $('[field=currency]');
            $currency.on('update', function () {
                self._setCurrency();
            });
            framework.hideLoading();
        });
    },

    _onAcceptCardNumber: function () {
        this._getInstallment();
        const card = this.card.number._.masked.currentMask;
        this.card.type = card.name;
        if (card.icon) {
            this.card.icon.html = card.icon;
            this.card.icon.$.addClass('show');
        } else {
            this.card.icon.html = '';
            this.card.icon.$.removeClass('show');
        }

        if (this.card.sample.exist) {
            this.card.preview.html = card.preview;
            
            $('.lightcolor').each(function (i, e) {
                e.setAttribute('class', 'lightcolor ' + card.color);
            });
            $('.darkcolor').each(function (i, e) {
                e.setAttribute('class', 'darkcolor ' + card.color + 'dark');
            });

            if (!card.icon) {
                this.card.icon.$.removeClass('show');
            } else {
                this.card.icon.$.addClass('show');
            }
        }
    },

    _onAcceptDate: function () {
        try {
            if (!this.card.date.value) {
                document.getElementById('svgexpire').innerHTML = '01/25';
            } else {
                document.getElementById('svgexpire').innerHTML = this.card.date.value;
            }
        } catch {}
    },

    _onAcceptCode: function () {
        try {
            if (!this.card.code.value) {
                document.getElementById('svgsecurity').innerHTML = '985';
            } else {
                document.getElementById('svgsecurity').innerHTML = this.card.code.value;
            }
        } catch {}
    },
    
    _onClickCardSample: function () {
        if (this.card.sample.$.hasClass('flipped')) {
            this._onFocusCardFront();
        } else {
            this._onFocusCardBack();
        }
    },

    _onClickPaymentTerms: async function (ev) {
        if (ev.target.tagName == 'SPAN' || ev.target.tagName == 'INPUT') {
            return;
        }

        ev.stopPropagation();
        ev.preventDefault();

        const self = this;
        if (!this.terms.content) {
            await rpc.query({
                route: '/payment/card/terms',
                params: {
                    partner: this.partner.value,
                }
            }).then(function (result) {
                self.terms.content = result;
            }).guardedCatch(function (error) {
                self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
                if (config.isDebug()) {
                    console.error(error);
                }
            });
        }

        if (this.terms.content) {
            const popup = new dialog(this, {
                title: _t('Terms & Conditions'),
                $content: $('<div/>').html(this.terms.content),
            });
            popup.open().opened(function () {
                popup.$modal.addClass('payment-page');
            });
        }
    },

    _onClickInstallmentTable: async function (ev) {
        ev.stopPropagation();
        ev.preventDefault();

        const self = this;
        if (!this.installment.grid) {
            await rpc.query({
                route: '/payment/card/installments',
                params: {
                    partner: this.partner.value,
                    campaign: this.campaign.name.value,
                    amount: this.amount.value,
                    rate: this.discount.single.value,
                    currency: this.currency.id,
                },
            }).then(function (result) {
                if ('error' in result) {
                    self.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('An error occured.') + ' ' + result.error,
                    });
                } else {
                    self.installment.grid = result;
                }
            }).guardedCatch(function (error) {
                self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
                if (config.isDebug()) {
                    console.error(error);
                }
            });
        }

        if (this.installment.grid) {
            const popup = new dialog(this, {
                title: _t('Installments Table'),
                $content: qweb.render('paylox.installment.grid', {
                    value: this.amount.value,
                    format: format,
                    ...this.currency,
                    ...this.installment.grid,
                }),
            });
            popup.open().opened(function () {
                popup.$modal.addClass('payment-page');
                $('.installment-table picture > img').on('load', function () {
                    $(this).removeClass('d-none');
                    $('.installment-table picture').removeClass('placeholder');
                });
            });
        }
    },

    _onClickCampaingTable: async function (ev) {
        ev.stopPropagation();
        ev.preventDefault();

        const self = this;
        if (!this.campaign.list) {
            await rpc.query({
                route: '/payment/card/campaigns',
            }).then(function (result) {
                self.campaign.list = result;
            }).guardedCatch(function (error) {
                self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
                if (config.isDebug()) {
                    console.error(error);
                }
            });
        }

        if (this.campaign.list) {
            const popup = new dialog(self, {
                title: _t('Campaigns Table'),
                size: 'small',
                buttons: [{
                    text: _t('Cancel'),
                    classes: 'btn-secondary text-white',
                    close: true,
                }],
                $content: qweb.render('paylox.campaigns', { campaigns: this.campaign.list, current: this.campaign.name.value })
            });

            popup.open().opened(function () {
                popup.$modal.addClass('payment-page');
                const $button = $('.modal-body button.o_button_select_campaign');
                $button.click(function(e) {
                    const campaign = e.currentTarget.dataset.name;
                    $('span#campaign').html(campaign || '-');
                    self.campaign.name.value = campaign;
                    self._getInstallment(true);
                    popup.destroy();
                });
            });
        }
    },

    _onClickRow: function (ev) {
        if (this.installment.row.$.data('type') === 'installment') {
            const $rows = this.installment.row.$.find('div');
            $rows.removeClass('installment-selected');
            $rows.find('input').prop({'checked': false});

            const $el = $(ev.target).closest('div.installment-line');
            $el.addClass('installment-selected');
            $el.find('input').prop({'checked': true});
        } else if (this.installment.row.$.data('type') === 'campaign') {
            const $el = $(ev.target).closest('div.installment-cell');
            if (!$el.length) {
                return;
            }

            const $cells = this.installment.row.$.find('div.installment-cell');
            $cells.removeClass('installment-selected');
            $cells.find('input').prop({'checked': false});

            $el.addClass('installment-selected');
            const $input = $el.find('input');
            $input.prop({'checked': true});

            this.campaign.name.value = $input.data('campaign');
        }
    },

    _onInputHolder: function () {
        try {
            if (this.card.holder.value) {
                document.getElementById('svgname').innerHTML = this.card.holder.value;
                document.getElementById('svgnameback').innerHTML = this.card.holder.value;
            } else {
                document.getElementById('svgname').innerHTML = '';
                document.getElementById('svgnameback').innerHTML = '';
            }
        } catch {}
    },

    _onInputAmount: function () {
        if (this.card.bin && this.installment.type) {
            this.installment.row.html = qweb.render('paylox.installment.row', {
                type: this.installment.type,
                rows: this.installment.rows,
                value: this.amount.value,
                s2s: this.payment.s2s.value,
                format: format,
                ...this.currency,
            });
        }
    },

    _onUpdateAmount: function () {
        this.amount._.updateValue();
        this._onInputAmount();
    },

    _onFocusCardFront: function () {
        if (this.card.sample.exist) {
            this.card.sample.$.removeClass('flipped');
        }
    },

    _onFocusCardBack: function () {
        if (this.card.sample.exist) {
            this.card.sample.$.addClass('flipped');
        }
    },

    _getInstallment: async function (force=false) {
        const self = this;
        if (force) {
            this.card.bin = '';
        }
 
        if (!this.card.number.value) {
            if (self.card.sample.exist) {
                document.getElementById('svgnumber').innerHTML = '0123 4567 8910 1112';
            }

            this.installment.colempty.$.removeClass('d-none');
            this.installment.col.$.addClass('d-none');
            this.installment.col.html = '';
            this.installment.cols = [];

            this.installment.rowempty.$.removeClass('d-none');
            this.installment.row.$.addClass('d-none');
            this.installment.row.html = '';
            this.installment.rows = [];

            this.card.logo.$.removeClass('show');
            this.card.family = '';
            this.card.bin = '';
        } else {
            if (this.card.sample.exist) {
                document.getElementById('svgnumber').innerHTML = this.card.number._.value;
            }

            if (this.card.number.value.length >= 6){
                const bin = this.card.number.value.substring(0, 6);
                if (this.card.bin !== bin) {
                    await rpc.query({
                        route: '/payment/card/installment',
                        params: {
                            bin: bin,
                            partner: this.partner.value,
                            campaign: this.campaign.name.value,
                            amount: this.amount.value,
                            rate: this.discount.single.value,
                            currency: this.currency.id,
                        },
                    }).then(function (result) {
                        if ('error' in result) {
                            self.installment.colempty.$.removeClass('d-none');
                            self.installment.col.$.addClass('d-none');
                            self.installment.col.html = '';
                            self.installment.rowempty.$.removeClass('d-none');
                            self.installment.row.$.addClass('d-none');
                            self.installment.row.html = '';
                            self.displayNotification({
                                type: 'warning',
                                title: _t('Warning'),
                                message: _t('An error occured.') + ' ' + result.error,
                            });
                        } else {
                            if (result.type === 'campaign') {
                                self.installment.colempty.$.addClass('d-none');
                                self.installment.col.$.removeClass('d-none');
                                self.installment.col.html = qweb.render('paylox.installment.col', {
                                    type: result.type,
                                    cols: result.cols,
                                    s2s: self.payment.s2s.value,
                                });
                            }
                            self.installment.cols = result.cols;

                            self.installment.type = result.type;
                            self.installment.rowempty.$.addClass('d-none');
                            self.installment.row.$.removeClass('d-none');
                            self.installment.row.html = qweb.render('paylox.installment.row', {
                                type: result.type,
                                rows: result.rows,
                                value: self.amount.value,
                                s2s: self.payment.s2s.value,
                                format: format,
                                ...self.currency,
                            });
                            self.installment.rows = result.rows;

                            if (result.family) {
                                self.card.logo.html = '<img src="' + result.logo + '" alt="' + result.family + '"/>';
                                self.card.logo.$.addClass('show');
                                self.card.family = result.family;
                            } else {
                                self.card.logo.html = '';
                                self.card.logo.$.removeClass('show');
                                self.card.family = '';
                            }
                            self.card.bin = bin;
                        }
                    }).guardedCatch(function (error) {
                        self.displayNotification({
                            type: 'danger',
                            title: _t('Error'),
                            message: _t('An error occured. Please contact with your system administrator.'),
                        });
                        if (config.isDebug()) {
                            console.error(error);
                        }
                    });
                }
            } else {
                this.installment.colempty.$.removeClass('d-none');
                this.installment.col.$.addClass('d-none');
                this.installment.col.html = '';
                this.installment.cols = [];

                this.installment.rowempty.$.removeClass('d-none');
                this.installment.row.$.addClass('d-none');
                this.installment.row.html = '';
                this.installment.rows = [];

                this.card.logo.html = '';
                this.card.logo.$.removeClass('show');
                this.card.bin = '';
                this.card.family = '';
            }
        }
    },

    _getInstallmentInput: function () {
        return $('.installment-cell input:checked');
    },

    _checkData: function () {
        if (!this.amount.value) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please enter an amount'),
            });
            this._enableButton();
            return false;
        } else if (!this.card.holder.value) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card holder name'),
            });
            this._enableButton();
            return false;
        } else if (!this.card.number.value) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card number'),
            });
            this._enableButton();
            return false;
        } else if (!this.card.date.value) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card expiration date'),
            });
            this._enableButton();
            return false;
        } else if (!this.card.code.value) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card security code'),
            });
            this._enableButton();
            return false;
        } else if (!this._getInstallmentInput().length) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please select whether payment is straight or installment'),
            });
            this._enableButton();
            return false;
        } else if (this.terms.ok.exist && !this.terms.ok.checked) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please accept Terms & Conditions'),
            });
            this._enableButton();
            return false;
        } else {
            return true;
        }
    },

    _enableButton: function () {
        if (this.payment.order.exist) {
            const widget = _.find(this.getParent().getChildren(), w => w.selector === 'form[name="o_payment_checkout"]');
            if (widget) {
                widget._enableButton();
                $('body').unblock();
            }
        }
    },

    _getParams: function () {
        const $input = this._getInstallmentInput();
        return {
            card: {
                type: this.card.type || '',
                family: this.card.family || '',
                code: this.card.code.value,
                holder: this.card.holder.value,
                date: this.card.date.value,
                number: this.card.number.value,
            },
            amount: this.amount.value,
            currency: this.currency.id,
            discount: {
                single: this.discount.single.value,
            },
            installment: {
                id: $input.data('id'),
                index: $input.data('index'),
                rows: this.installment.rows,
            },
            campaign: this.campaign.name.value,
            successurl: this.payment.successurl.value,
            failurl: this.payment.failurl.value,
            partner: parseInt(this.partner.value || 0),
            order: this.payment.order.value,
            invoice: this.payment.invoice.value,
            subscription: this.payment.subscription.value,
        }
    },

    _onClickPaymentButton: async function () {
        const self = this;
        if (this._checkData()) {
            framework.showLoading();
            await rpc.query({
                route: '/payment/card/pay',
                params: this._getParams(),
            }).then(function (result) {
                if ('url' in result) {
                    window.location.assign(result.url);
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: _t('An error occured.') + ' ' + result.error,
                    });
                    framework.hideLoading();
                }
            }).guardedCatch(function (error) {
                self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
                if (config.isDebug()) {
                    console.error(error);
                }
                self._enableButton();
                framework.hideLoading();
            });
        }
    },
});

publicWidget.registry.payloxPaymentTransaction = publicWidget.Widget.extend({
    selector: '.payment-transaction',

    start: function () {
        return this._super.apply(this, arguments).then(function () {
            $('.table-fold tr.row-view').on('click', function() {
                $(this).toggleClass('open').next('.row-fold').toggleClass('open');
            });
        });
    },
});

export default publicWidget.registry.payloxPage;