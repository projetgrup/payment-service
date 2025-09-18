/** @odoo-module alias=paylox.page **/
'use strict';

import { _t, qweb } from 'web.core';
import config from 'web.config';
import rpc from 'web.rpc';
import dialog from 'web.Dialog';
import publicWidget from 'web.public.widget';
import fields from 'paylox.fields';
import { format, search } from 'paylox.tools';
import framework from 'paylox.framework';
import cardPrograms from 'paylox.card.programs';

publicWidget.registry.payloxPage = publicWidget.Widget.extend({
    selector: '#payment_card',
    jsLibs: ['/payment_jetcheckout/static/src/lib/imask/imask.js'],
    xmlDependencies: ['/payment_jetcheckout/static/src/xml/templates.xml'],

    init: function (parent, options) {
        this._super(parent, options);
        const self = this;
        this.card = {
            number: new fields.string({
                events: [
                    ['focus', this._onFocusCardFront],
                    ['accept', this._onAcceptCardNumber],
                ],
                mask: {
                    mask: cardPrograms,
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
            token: {
                select: new fields.selection({
                    events: [['change', this._onChangeCardTokenSelect]],
                    formatResult: (token) => {
                        return qweb.render('paylox.token.select', { search, ...token } );
                    },
                    formatSelection: (token) => {
                        return qweb.render('paylox.token.select', { search, ...token });
                    },
                    minimumResultsForSearch: Infinity,
                    data: function() {
                        const $data = $('[field="card.token.data"]');
                        if ($data.length) {
                            const value = $data.val();
                            $data.remove();
                            if (value) {
                                return JSON.parse(atob(value));
                            }
                        }
                        return [];
                    },
                }),
                radio: new fields.element({
                    events: [['start', function() {
                        let tokens = [];
                        const $data = $('[field="card.token.data"]');
                        if ($data.length) {
                            const value = $data.val();
                            $data.remove();
                            if (value) {
                                tokens = JSON.parse(atob(value));
                                self.card.token.value = 0;
                            }
                        }
                        this.card.token.radio.html = qweb.render('paylox.token.radio', { search, tokens });
                        this.card.token.radio.$.find('button').each(function() {
                            const $button = $(this);
                            const $input = $button.find('input');
                            $button.click(function() {
                                $('input[name="card-token-radio"]').prop('checked', false);
                                $input.prop('checked', true);

                                self.card.token.text = $input.data('value') || '';
                                self.card.token.value = $input.val();
                                if ($.isNumeric(self.card.token.value)) {
                                    self.card.token.value = Number(self.card.token.value);
                                }
                                self._onChangeCardToken();
                            });

                            $button.find('.card-token-remove').on('click', function(ev) {
                                ev.stopPropagation();
                                ev.preventDefault();

                                const popup = new dialog(self, {
                                    title: _t('Are you sure?'),
                                    $content: $('<div/>').text(_t('This action cannot be undone.')),
                                    size: 'small',
                                    technical: false,
                                    buttons: [{
                                        text: _t('Cancel'),
                                        classes: 'btn-secondary text-white',
                                        close: true,
                                    }, {
                                        text: _t('Remove'),
                                        classes: 'btn-danger text-white',
                                        click: () => {
                                            $button.find('.card-token-loading').addClass('show');
                                            $button.find('.card-token-radio-add').click();
                                            popup.destroy();
                                            rpc.query({
                                                route: '/payment/card/remove',
                                                params: { token: $input.val() },
                                            }).then((res) => {
                                                if (res.error) {
                                                    self.displayNotification({
                                                        type: 'danger',
                                                        title: _t('Error'),
                                                        message: _t('An error occured. Please contact with your system administrator.'),
                                                    });
                                                } else {
                                                    $button.remove();
                                                }
                                            }).guardedCatch((error) => {
                                                $button.find('.card-token-loading').removeClass('show');
                                                if (!ev?.detail?.noWarning) {
                                                    self.displayNotification({
                                                        type: 'danger',
                                                        title: _t('Error'),
                                                        message: _t('An error occured. Please contact with your system administrator.'),
                                                    });
                                                }
                                            });
                                        },
                                    }],
                                });
                                popup.open();
                            });
                        });
                    }]],
                }),
                data: new fields.element(),
                value: -1,
                text: '',
            },
            point: new fields.element({
                events: [['click', this._onClickCardPoint]],
            }),
            preview: new fields.string(),
            type: '',
            family: '',
            program: '',
            bin: '',
            valid: false,
        };
        this.campaign = {
            name: new fields.string({
                events: [['change', this._onChangeCampaign]],
            }),
            table: new fields.string({
                events: [['click', this._onClickCampaingTable]],
            }),
            text: new fields.string(),
            locked: false,
        };
        this.currency = {
            id: 0,
            decimal: 2,
            name: '',
            separator: '.',
            thousand: ',',
            position: 'after',
            symbol: '',
        };
        this.description = new fields.string();
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
            row: new fields.string({
                events: [['click', this._onClickRow]],
            }),
            table: new fields.string({
                events: [['click', this._onClickInstallmentTable]],
            }),
            credit: new fields.string({
                events: [['click', this._onClickInstallmentCredit]],
            }),
            rowempty: new fields.string(),
            col: new fields.string(),
            colempty: new fields.string(),
            summary: new fields.element(),
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
        this.type = {
            all: new fields.element({
                events: [['click', this._onClickPaymentType]],
            }),
            transfer: new fields.element({
                events: [['click', this._onClickPaymentTypeTransfer]],
            }),
            wallet: new fields.element({
                events: [['click', this._onClickPaymentTypeWallet]],
            }),
            credit: new fields.element({
                events: [['click', this._onClickPaymentTypeCredit]],
            }),
        }
        this.payment = {
            button: new fields.element({
                events: [['click', this._onClickPaymentButton]],
            }),
            form: new fields.string({
                events: [['click', this._onClickPaymentButton]],
            }),
            contactless: new fields.element({
                events: [['click', this._onClickPaymentContactless]],
            }),
            successurl: new fields.string(),
            failurl: new fields.string(),
            s2s: new fields.boolean({
                default: false,
            }),
            order: new fields.integer(),
            invoice: new fields.integer(),
            subscription: new fields.integer(),
            initWarningCommission: new fields.boolean({
                default: false,
            }),
        };
        this.partner = new fields.integer({
            default: 0,
        });
        this.button = {
            currency: new fields.element({
                events: [['click', this._onClickAmountCurrency]],
            }),
        };
        Object.defineProperty(this.type, 'selected', {
            get () {
                return payment_type.querySelector('input[name="payment_type"]:checked').value;
            },
        });
        Object.defineProperty(this.type.transfer, 'selected', {
            get () {
                return payment_type_transfer.querySelector('input[name="payment_type_transfer"]:checked');
            },
        });
        Object.defineProperty(this.type.wallet, 'selected', {
            get () {
                return payment_type_wallet.querySelector('input[name="payment_type_wallet"]:checked');
            },
        });
        Object.defineProperty(this.type.credit, 'selected', {
            get () {
                return payment_type_credit.querySelector('input[name="payment_type_credit"]:checked');
            },
        });
        Object.defineProperty(this.installment.credit, 'selected', {
            get () {
                const credit = payment_type_credit.querySelector('input:checked').closest('[field="type.credit"]');
                return credit.querySelector('.installment-line input:checked');
            },
        });
        Object.defineProperty(this.installment.credit, 'rows', {
            get () {
                const credit = payment_type_credit.querySelector('input:checked').closest('[field="type.credit"]');
                const rows = credit.querySelectorAll('.installment-line input');
                const result = [];
                for (const row of rows) {
                    const id = parseInt(row.dataset.id);
                    const crate = parseFloat(row.dataset.crate);
                    const corate = parseFloat(row.dataset.corate);
                    result.push({
                        id: id,
                        count: id,
                        crate: crate || 0,
                        corate: corate || 0,
                    })
                }
                return result;
            },
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
        const mask = {
            mask: Number,
            min: 0,
            signed: false,
            normalizeZeros: true,
            padFractionalZeros: true,
            scale: this.currency.decimal,
            radix: this.currency.separator,
            mapToRadix: [],
            thousandsSeparator: this.currency.thousand,
        }
        if (window.location.pathname.includes('/p/')) {
            delete mask.min;
            delete mask.signed;
        }
        return mask;
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

    _start: function (...fields) {
        const t = this;
        let fs = $();
        let z = [];
        let r = [];
        if (fields.length) {
            for (let f of fields) {
                let tag = `[field="${f}"]`;
                let el = $(tag);
                if (el.length) {
                    fs = fs.add(tag);
                } else {
                    const ids = f.split('.');
                    if (!ids.length) {
                        return;
                    }

                    try {
                        let i = 0;
                        let s = t;
                        let l = ids.length - 1;
                        while (i < l) {
                            const id = ids[i];
                            s = s[id];
                            i++;
                        }
                        s[ids[l]].$ = $();
                    } catch {}
                }
            }
        } else {
            fs = $('[field]');
        }

        fs.each(function(_, e) {
            const n = e.getAttribute('field');
            const ids = n.split('.');
            if (!ids.length) {
                return;
            }

            try {
                let i = 0;
                let s = t;
                let l = ids.length - 1;

                while (i < l) {
                    const id = ids[i];
                    s = s[id];
                    i++;
                }

                if (fields.length) {
                    if (!(r.includes(n))) {
                        s[ids[l]].$ = $();
                        r.push(n);
                    }
                }

                s[ids[l]].$ = s[ids[l]].$.add(e);
                z.push([s[ids[l]], t, n]);
            } catch {}
        });

        for (const a of z) {
            a[0].start(a[1], a[2], fields.length);
        };
    },
 
    start: function () {
        window.addEventListener('field-updated', (ev) => {
            if (Array(ev.detail)) {
                this._start(ev.detail);
            }
        });
        return this._super.apply(this, arguments).then(() => {
            this._setCurrency();
            this._start();
            if (this.payment.initWarningCommission.exist) {
                const node = this.payment.initWarningCommission.$;
                this.payment.initWarningCommission = JSON.parse(this.payment.initWarningCommission.value);
                node.remove();
            } else {
                this.payment.initWarningCommission = false;
            }
            const $currency = $('[field=currency]');
            $currency.on('update', () => {
                this._setCurrency();
            });
            if (this.card.number.exist) {
                this._onAcceptCardNumber({ detail: { noWarning: true } });
            }
            framework.hideLoading();
        });
    },

    _onAcceptCardNumber: function (ev) {
        this._getInstallment();
        const card = this.card.number._.masked.currentMask;
        const limit = card.code === 'amex' ? 14 : 15;
        this.card.program = card.name;

        if (card.typedValue.length > limit) {
            rpc.query({
                route: '/payment/card/valid',
                params: { number: card.typedValue },
            }).then((valid) => {
                this.card.valid = valid;
                if (!valid && !ev?.detail?.noWarning) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter a valid card number'),
                    });
                }
            }).guardedCatch((error) => {
                this.card.valid = false;
                if (!ev?.detail?.noWarning) {
                    this.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: _t('An error occured. Please contact with your system administrator.'),
                    });
                }
            });
        }

        if (card.icon) {                                       
            this.card.icon.html = `<img src="data:image/svg+xml;base64,${card.icon}" alt="${card.name}"/>`;
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

    _onChangeCampaign: function (ev, { locked }={}) {
        this.campaign.locked = locked;
        let campaign = $(ev.currentTarget).val();
        $('span#campaign').html(campaign || '-');
        if (this.installment.row.$.data('type') === 'i') {
            this._getInstallment(true);
            this.installment.grid = null;
        }
    },

    _onChangeCardToken: function () {
        if (isNaN(Number(this.card.token.value))) {
            $('.field-container.field-name').addClass('d-none');
            $('.field-container.field-number').addClass('d-none');
            $('.field-container.field-date').addClass('d-none');
            $('.field-container.field-code').addClass('d-none');
        } else {
            $('.field-container.field-name').removeClass('d-none');
            $('.field-container.field-number').removeClass('d-none');
            $('.field-container.field-date').removeClass('d-none');
            $('.field-container.field-code').removeClass('d-none');
            $('.field-container.field-name input').focus();

            const $el = $('.card-token-radio-add');
            if ($el.length) {
                $('html, body').animate({ scrollTop: $el.position().top + 72 }, 1000);
            }
        }
        this._getInstallment();
    },

    _onChangeCardTokenSelect: function () {
        let option = this.card.token.select.options.data.at(-1);
        let value = this.card.token.select.value;
        this.card.token.value = value;
        this.card.token.text = option?.children?.find(c => c.id === value)?.text || '';
        this._onChangeCardToken();
    },

    _onClickAmountCurrency: function (ev) {
        if (ev.target.nodeName === 'LI') {
            this._updateCurrency(ev.target);
            this._setCurrency();
            const $symbol = $('.amount .symbol');
            $symbol.removeClass('symbol-after symbol-before').addClass('symbol-' + ev.target.dataset.position);
            $symbol.text(ev.target.dataset.symbol);
            this.button.currency.$.find('span').text(ev.target.dataset.name);
            this._getInstallment(true);
            this.installment.grid = null;
        }
    },

    _onClickCardSample: function () {
        if (this.card.sample.$.hasClass('flipped')) {
            this._onFocusCardFront();
        } else {
            this._onFocusCardBack();
        }
    },

    _onClickCardTokenPopup: async function () {
        ev.stopPropagation();
        ev.preventDefault();
        
        if (true) {
            await rpc.query({
                route: '/payment/card/point',
                params: {        
                    code: this.card.code.value,
                    date: this.card.date.value,
                    holder: this.card.holder.value,
                    number: this.card.number.value,
                    currency: this.currency.id,
                }
            }).then((result) => {
                this.displayNotification({
                    type: 'info',
                    title: _t('Info'),
                    message: result,
                });
            }).guardedCatch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
                if (config.isDebug()) {
                    console.error(error);
                }
            });
        }

        const popup = new dialog(this, {
            title: _t('Saved Cards'),
            $content: qweb.render('paylox.tokens', {}),
        });
        popup.open();
    },

    _onClickCardPoint: async function (ev) {
        ev.stopPropagation();
        ev.preventDefault();

        if (true) {
            await rpc.query({
                route: '/payment/card/point',
                params: {        
                    code: this.card.code.value,
                    date: this.card.date.value,
                    holder: this.card.holder.value,
                    number: this.card.number.value,
                    currency: this.currency.id,
                }
            }).then((result) => {
                this.displayNotification({
                    type: 'info',
                    title: _t('Info'),
                    message: result,
                });
            }).guardedCatch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
                if (config.isDebug()) {
                    console.error(error);
                }
            });
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
            }).then((result) => {
                if ('error' in result) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('An error occured.') + ' ' + result.error,
                    });
                } else {
                    this.installment.grid = result;
                }
            }).guardedCatch(() => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
            });
        }

        if (this.installment.grid) {
            const popup = new dialog(this, {
                size: 'extra-large',
                title: _t('Installments Table'),
                $content: qweb.render('paylox.installment.grid', {
                    value: this.amount.value,
                    format: {...format, type: this._getCardType},
                    ...this.currency,
                    ...this.installment.grid,
                }),
            });
            popup.open().opened(() => {
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

        if (!this.campaign.list) {
            await rpc.query({
                route: '/payment/card/campaigns',
            }).then((result) => {
                this.campaign.list = result;
            }).guardedCatch(() => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
            });
        }

        if (this.campaign.list) {
            const popup = new dialog(this, {
                title: _t('Campaigns Table'),
                size: 'small',
                buttons: [{
                    text: _t('Cancel'),
                    classes: 'btn-secondary text-white',
                    close: true,
                }],
                $content: qweb.render('paylox.campaigns', {
                    campaigns: this.campaign.list,
                    current: this.campaign.name.value,
                })
            });

            popup.open().opened(() => {
                popup.$modal.addClass('payment-page');
                const $button = $('.modal-body button.o_button_select_campaign');
                $button.click((e) => {
                    const campaign = e.currentTarget.dataset.name;
                    this.campaign.name.value = campaign;
                    this.campaign.name.$.trigger('change');
                    popup.destroy();
                });
            });
        }
    },

    _onClickRow: function (ev) {
        if (this.installment.row.$.data('type') === 'i') {
            const $rows = this.installment.row.$.find('div');
            $rows.removeClass('installment-selected');
            $rows.find('input').prop({'checked': false});

            const $el = $(ev.target).closest('div.installment-line');
            $el.addClass('installment-selected');
            $el.find('input').prop({'checked': true});
        } else if (this.installment.row.$.data('type') === 'c') {
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
            this.campaign.name.$.trigger('change');
        } else if (this.installment.row.$.data('type') === 'ct') {
            const $rows = this.installment.row.$.find('div');
            $rows.removeClass('installment-selected');
            $rows.find('input').prop({'checked': false});

            const $el = $(ev.target).closest('div.installment-line');
            $el.addClass('installment-selected');
            const $input = $el.find('input');
            $input.prop({'checked': true});

            this.campaign.name.value = $input.data('campaign');
            this.campaign.name.$.trigger('change');
        }
    },

    _onClickInstallmentCredit: function (ev) {
        const $rows = this.installment.credit.$.find('div');
        $rows.removeClass('installment-selected');
        $rows.find('input').prop({'checked': false});

        const $el = $(ev.target).closest('div.installment-line');
        $el.addClass('installment-selected');
        $el.find('input').prop({'checked': true});
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

        if (this.installment.credit.exist) {
            this.installment.credit.$.each((_, e) => {
                const $e = $(e);
                const $row = $e.find('.installment-line');
                const $amount = $row.find('[name=payment_type_credit_installment_amount]'); 
                const $total = $row.find('[name=payment_type_credit_installment_total]'); 
                const count = Number($row.data('id') || 1);
                const rate = Number($row.data('rate') || 0);
                const amount = this.amount.value * (1 + (rate/100));
                const currency = [this.currency.position, this.currency.symbol, this.currency.decimal];
                $amount.html(format.currency(amount/count, ...currency));
                $total.html(format.currency(amount, ...currency));
            });
        }
    },

    _onUpdateAmount: function () {
        this.amount._.updateValue();
        this.amount.$.data('value', this.amount.value);
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

    _getCardType: function (type) {
        switch (type) {
            case 'Credit':
                return _t('Credit Card');
            case 'Debit':
                return _t('Debit Card');
            case 'Credit-Business':
                return _t('Business Card');
            default:
                return _t('General');
        }
    },

    _getInstallment: async function (force=false) {
        const self = this;
        if (force) {
            this.card.bin = '';
        }
 
        const tokenValue = this.card.token.value;
        const numberValue = this.card.number.value;
        if (!isNaN(Number(tokenValue)) && !numberValue) {
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
            this.card.type = '';
            this.card.bin = '';
        } else {
            if (this.card.sample.exist) {
                document.getElementById('svgnumber').innerHTML = this.card.number._.value;
            }

            if (isNaN(Number(tokenValue)) || numberValue.length >= 6) {
                let bin;
                if (isNaN(Number(tokenValue))) {
                    bin = this.card.token.text.substring(0, 6);
                } else {
                    bin = numberValue.substring(0, 6);
                }
                if (this.card.bin !== bin) {
                    await rpc.query({
                        route: '/payment/card/installment',
                        params: {
                            bin: bin,
                            token: tokenValue,
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
                            if (result.type === 'c') {
                                self.installment.colempty.$.addClass('d-none');
                                self.installment.col.$.removeClass('d-none');
                                self.installment.col.html = qweb.render('paylox.installment.col', {
                                    type: result.type,
                                    cols: result.cols,
                                    s2s: self.payment.s2s.value,
                                    //hideRate: self.payment.hideRate.value,
                                });
                            }
                            self.installment.cols = result.cols;
                            self.installment.rows = result.rows;
                            self.installment.type = result.type;
                            self.installment.rowempty.$.addClass('d-none');
                            self.installment.row.$.removeClass('d-none');
                            self.installment.row.html = qweb.render('paylox.installment.row', {
                                type: result.type,
                                rows: result.rows,
                                value: self.amount.value,
                                s2s: self.payment.s2s.value,
                                //hideRate: self.payment.hideRate.value,
                                format: format,
                                ...self.currency,
                            });

                            self.installment.row.$.find('.installment-selected').trigger('click');

                            if (self.installment.summary.exist) {
                                self.installment.summary.html = qweb.render('paylox.installment.summary', {
                                    row: result.rows?.[0] || {},
                                    value: self.amount.value,
                                    format: format,
                                    ...self.currency,
                                });
                            }

                            if (result.card) {
                                if (result.card.family) {
                                    const cardFamily = search.family(result.card.family)?.icon;
                                    if (cardFamily) {
                                        self.card.logo.html = `<img src="data:image/svg+xml;base64,${cardFamily}" alt="${result.card.family}"/>`;
                                        self.card.logo.$.addClass('show');
                                    } else if (result.card.logo) {
                                        self.card.logo.html = `<img src="${result.card.logo}" alt="${result.card.family}"/>`;
                                        self.card.logo.$.addClass('show');
                                    }
                                    self.card.family = result.card.family;
                                } else {
                                    self.card.logo.html = '';
                                    self.card.logo.$.removeClass('show');
                                    self.card.family = '';
                                }
                                self.card.type = result.card.type || '';
                            }

                            self.card.bin = bin;
                            if (!self.campaign.locked) {
                                if (result.type[0] === 'c' && result.rows.length) {
                                    self.campaign.name.value = result.rows[0]['campaign'] || '';
                                    self.campaign.name.$.trigger('change');
                                } else {
                                    self.campaign.name.value = result.card?.campaign || '';
                                }
                                $('span#campaign').html(self.campaign.name.value || '-');
                            }
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

    _getInstallmentData: function () {
        const installment = $('.installment-cell input:checked');
        if (!installment.length) return {}
        return {
            id: installment.data('id') || 1,
            index: installment.data('index') || 0,
        }
    },

    _getInstallmentRow: function (id=0) {
        if (!id) {
            const installment = this._getInstallmentData();
            id = installment.id;
        }

        const rows = this.installment.rows || [];
        return rows.find(r => r.id === id);
    },

    _checkData: function () {
        let checked = true;
        const type = this.type.selected;
        if (type === 'virtual_pos') {
            if (!isNaN(Number(this.card.token.value))) {
                if (!(this.amount.value > 0)) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter an amount'),
                    });
                    checked = false;
                } else if (!this.card.holder.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please fill card holder name'),
                    });
                    checked = false;
                } else if (!this.card.number.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please fill card number'),
                    });
                    checked = false;
                } else if (!this.card.valid) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter a valid card number'),
                    });
                    checked = false;
                } else if (!this.card.date.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please fill card expiration date'),
                    });
                    checked = false;
                } else if (!this.card.code.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please fill card security code'),
                    });
                    checked = false;
                }
            }
            if ($('.installment-cell').length && !$('.installment-cell input:checked').length) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please select whether payment is straight or installment'),
                });
                checked = false;
            } else if (this.terms.ok.exist && !this.terms.ok.checked) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please accept Terms & Conditions'),
                });
                checked = false;
            }
        } else if (type === 'soft_pos') {
            if (!this.amount.value) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please enter an amount'),
                });
                checked = false;
            }
        } else if (type === 'transfer') {
            if (!this.amount.value) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please enter an amount'),
                });
                checked = false;
            } else if (!this.type.transfer.selected) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please select a bank'),
                });
                checked = false;
            }
        } else if (type === 'wallet') {
            if (!this.amount.value) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please enter an amount'),
                });
                checked = false;
            } else if (!this.type.wallet.selected) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please select a provider'),
                });
                checked = false;
            }
        } else if (type === 'credit') {
            if (!this.amount.value) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please enter an amount'),
                });
                checked = false;
            } else if (!this.type.credit.selected) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please select a bank'),
                });
                checked = false;
            }
        } else {
            checked = false;
        }

        if (!checked) {
            this._enableButton();
        }

        return checked;
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
        const type = this.type.selected;
        if (type === 'virtual_pos') {
            const $input = $('.installment-cell input:checked');
            return {
                type,
                card: {
                    type: this.card.type || '',
                    program: this.card.program || '',
                    family: this.card.family || '',
                    code: this.card.code.value,
                    holder: this.card.holder.value,
                    date: this.card.date.value,
                    number: this.card.number.value,
                    token: this.card.token.value,
                },
                amount: this.amount.value,
                currency: this.currency.id,
                discount: {
                    single: this.discount.single.value,
                },
                installment: {
                    id: $input.data('id') || 1,
                    index: $input.data('index') || 0,
                    rows: this.installment.rows || [],
                },
                description: this.description.value || '',
                campaign: this.campaign.name.value || '',
                partner: parseInt(this.partner.value || 0),
                successurl: this.payment.successurl.value,
                failurl: this.payment.failurl.value,
                order: this.payment.order.value,
                invoice: this.payment.invoice.value,
                subscription: this.payment.subscription.value,
            }
        } else if (type === 'soft_pos') {
            return {
                type,
                amount: this.amount.value,
                currency: this.currency.id,
                campaign: this.campaign.name.value,
                partner: parseInt(this.partner.value || 0),
                successurl: this.payment.successurl.value,
                failurl: this.payment.failurl.value,
                order: this.payment.order.value,
                invoice: this.payment.invoice.value,
                subscription: this.payment.subscription.value,
            }

        } else if (type === 'transfer') {
            return {
                type,
                name: this.type.transfer.selected.value,
                installment: {
                    index: 0,
                    id: 1,
                    rows: [{
                        id: 1,
                        count: 1,
                        crate: 0,
                        corate: 0,
                    }],
                },
                partner: parseInt(this.partner.value || 0),
                amount: this.amount.value,
                currency: this.currency.id,
                order: this.payment.order.value,
                invoice: this.payment.invoice.value,
                subscription: this.payment.subscription.value,
                successurl: this.payment.successurl.value,
                failurl: this.payment.failurl.value,
            }
        } else if (type === 'wallet') {
            return {
                type,
                id: this.type.wallet.selected.dataset.id,
                name: this.type.wallet.selected.value,
                installment: {
                    index: 0,
                    id: 1,
                    rows: [{
                        id: 1,
                        count: 1,
                        crate: 0,
                        corate: 0,
                    }],
                },
                partner: parseInt(this.partner.value || 0),
                amount: this.amount.value,
                currency: this.currency.id,
                order: this.payment.order.value,
                invoice: this.payment.invoice.value,
                subscription: this.payment.subscription.value,
                successurl: this.payment.successurl.value,
                failurl: this.payment.failurl.value,
            }
        } else if (type === 'credit') {
            return {
                type,
                code: this.type.credit.selected.value,
                installment: {
                    index: 0,
                    id: 1,
                    rows: [{
                        id: 1,
                        count: 1,
                        crate: 0,
                        corate: 0,
                    }],
                },
                partner: parseInt(this.partner.value || 0),
                campaign: this.type.credit.selected.dataset.campaign,
                amount: this.amount.value,
                currency: this.currency.id,
                order: this.payment.order.value,
                invoice: this.payment.invoice.value,
                subscription: this.payment.subscription.value,
                successurl: this.payment.successurl.value,
                failurl: this.payment.failurl.value,
            }
        }
        return {}
    },

    _onClickPaymentType: function (ev) {
        const el = ev.currentTarget;
        const code = el.dataset.name;

        el.querySelector('input').checked = true;
        $('div[id^=payment_type_]').each((_, e) => {
            if (e.id === `payment_type_${code}`) {
                e.classList.remove('d-none');
            } else {
                e.classList.add('d-none');
            }
        })
    },

    _onClickPaymentTypeTransfer: function (ev) {
        const id = ev.currentTarget.dataset.id;
        this.type.transfer.$.each((_, e) => {
            if (e.dataset.id === id) {
                e.classList.add('selected');
                e.querySelector('input').checked = true;
            } else {
                e.classList.remove('selected');
                e.querySelector('input').checked = false;
            }
        })
    },

    _onClickPaymentTypeWallet: function (ev) {
        const id = ev.currentTarget.dataset.id;
        this.type.wallet.$.each((_, e) => {
            if (e.dataset.id === id) {
                e.classList.add('selected');
                e.querySelector('input').checked = true;
            } else {
                e.classList.remove('selected');
                e.querySelector('input').checked = false;
            }
        })
    },

    _onClickPaymentTypeCredit: function (ev) {
        const id = ev.currentTarget.dataset.id;
        this.type.credit.$.each((_, e) => {
            if (e.dataset.id === id) {
                e.classList.add('selected');
                e.querySelector('input').checked = true;
            } else {
                e.classList.remove('selected');
                e.querySelector('input').checked = false;
            }
        })
    },

    _onClickPaymentButton: function (ev) {
        if (this._checkData()) {
            if (!ev?.detail?.noWarning && this.payment.initWarningCommission) {
                const installmentData = this._getInstallmentData();
                const installmentCount = installmentData.id || 1;
                const row = this._getInstallmentRow(installmentCount);
                const installmentRate = row?.crate || 0;
                if (installmentRate > 0) {
                    const advisor = (advice) => {
                        if (advice === 1) {
                            if (installmentCount === 1) {
                                return false;
                            } else {
                                const rows = this.installment.rows || [];
                                let index = rows.findIndex(r => r.id === installmentData.id);
                                while (index > 0) {
                                    index--;
                                    if (rows[index]['crate'] === 0) {
                                        return rows[index]['id'];
                                    }
                                }
                            }
                        } else if (advice === 2) {
                            let rowId = installmentCount;
                            let rowRate = installmentRate;
                            const rows = this.installment.rows || [];
                            for (const row of rows) {
                                if (!row.id || row.id === installmentCount || row.crate === 0) {
                                    continue;
                                } else {
                                    let monthlyRate = row.crate/row.id;
                                    if (rowRate >= monthlyRate) {
                                        rowId = row.id;
                                        rowRate = monthlyRate;
                                    }
                                }
                            }
                            if (rowId === installmentCount) {
                                return false;
                            }
                            return { id: rowId, rate: rowRate};
                        }
                        return false;
                    };
                    const popup = new dialog(this, {
                        title: _t('Warning'),
                        size: 'small',
                        $content: qweb.render('paylox.warning.commission', {
                            row,
                            format,
                            advisor,
                            warning: this.payment.initWarningCommission,
                            amount: this.amount.value,
                            ...this.currency,
                        }),
                        buttons: [{
                            text: _.str.sprintf(_t('Pay with %s installment(s)'), row.id),
                            classes: 'btn-primary btn-block font-weight-bold',
                            click: () => {
                                this._onClickPaymentButton({ detail: { noWarning: true } });
                                popup.destroy();
                            },
                        }, {
                            text: _t('Cancel'),
                            classes: 'btn-secondary btn-block font-weight-bold',
                            close: true,
                        }],
                    });
                    popup.open().opened(() => {
                        $('button[name=popupWarningCommissionButton]').click((e) => {
                            const id = e.currentTarget.dataset.id;
                            $('[field="installment.row"]').find(`input[name=${id}]`).closest('div.installment-line').click(); 
                            this._onClickPaymentButton({ detail: { noWarning: true } });
                            popup.destroy();
                        });
                    });
                    return false;
                };
            }

            framework.showLoading();
            //const href = window.location.href;
            //window.history.pushState({}, '', '/payment/redirect');
            return rpc.query({
                route: '/payment/init',
                params: this._getParams(),
            }).then((result) => {
                if ('url' in result) {
                    if (result.popup) {
                        this._openInitPopup(result.url, result.id);
                    } else {
                        window.location.assign(result.url);
                    }
                } else {
                    this.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: _t('An error occured.') + ' ' + result.error,
                    });
                    if (result.reload) {
                        window.location.reload();
                    }
                    //window.history.pushState({}, '', href);
                    framework.hideLoading();
                }
            }).guardedCatch(() => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
                this._enableButton();
                //window.history.pushState({}, '', href);
                framework.hideLoading();
            });
        }
        return false;
    },

    _openInitWindow: function(url, transactionId) {
        const self = this;
        
        const popup = window.open(
            url,
            '3DSecurePopup',
            'width=600,height=500,scrollbars=yes,resizable=yes,status=yes,location=yes'
        );
        
        if (!popup) {
            window.location.assign(url);
            return;
        }
        const checkPopup = setInterval(() => {
            if (popup.closed) {
                clearInterval(checkPopup);
                rpc.query({
                    route: '/payment/status/' + transactionId,
                    params: {}
                }).then((result) => {
                    if (result.status === 'done') {
                        window.location.assign('/my/ads?step=5');
                    } else if (result.status === 'error' || result.status === 'cancel') {
                        framework.hideLoading();
                        self.displayNotification({
                            type: 'danger',
                            title: _t('Payment Failed'),
                            message: _t('Your payment could not be processed. Please try again.'),
                        });
                    } else {
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    }
                }).guardedCatch(() => {
                    framework.hideLoading();
                    self.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: _t('An error occurred while checking payment status.'),
                    });
                });
            }
        }, 1000);
        
        setTimeout(() => {
            if (!popup.closed) {
                popup.close();
                clearInterval(checkPopup);
                framework.hideLoading();
                self.displayNotification({
                    type: 'warning',
                    title: _t('Timeout'),
                    message: _t('Payment process timed out. Please try again.'),
                });
            }
        }, 600000);
    },

    _openInitPopup: function(url, txid) {
        const popup = new dialog(this, {
            $content: qweb.render('paylox.init.popup', { url }),
            dialogClass: 'o_payment_init_popup',
            technical: false,
        });
        popup.open();
        popup.on_detach_callback = () => {
            framework.hideLoading();
        };
    },

    _onClickPaymentContactless: function() {
        return this._onClickPaymentButton();
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
