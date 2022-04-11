odoo.define('payment_jetcheckout.payment_page', function (require) {
"use strict";

var config = require('web.config');
var core = require('web.core');
var publicWidget = require('web.public.widget');
var rpc = require('web.rpc');
var utils = require('web.utils');
var dialog = require('web.Dialog');
var cards = require('payment_jetcheckout.payment_card');

var round_di = utils.round_decimals;
var qweb = core.qweb;
var _t = core._t;

publicWidget.registry.JetcheckoutPaymentPage = publicWidget.Widget.extend({
    selector: '.payment-card',
    xmlDependencies: ['/payment_jetcheckout/static/src/xml/templates.xml'],

    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.$name = document.getElementById('name');
            self.$cardnumber = document.getElementById('cardnumber');
            self.$expirationdate = document.getElementById('expirationdate');
            self.$securitycode = document.getElementById('securitycode');
            self.$ccicon = document.getElementById('ccicon');
            self.$ccsingle = document.getElementById('ccsingle');
            self.$ccname = document.getElementById('ccname');
            self.$ccfamily = document.getElementById('ccfamily');
            self.$amount = document.getElementById('amount');
            self.$amount_installment = document.getElementById('amount_installment');
            self.$currency = document.getElementById('currency');
            self.$accept_terms = document.getElementById('accept_terms');
            self.$payment_terms = document.querySelector('.terms-container');
            self.$commission = document.getElementById('commission');
            self.$row = document.getElementById('installment_row');
            self.$empty = document.getElementById('installment_empty');
            self.$svgnumber = document.getElementById('svgnumber');
            self.$creditcard = document.querySelector('.creditcard');
            self.$installments_table = document.getElementById('installments_table');
            self.$cclogo = document.getElementById('installment_card');
            self.$payment_pay = document.getElementById('payment_pay');
            self.$payment_pay0 = document.getElementById('payment_pay0');
            self.$payment_pay1 = document.getElementById('payment_pay1');
            self.$payment_form = document.getElementById('o_payment_form_pay');
            self.$success_url = document.getElementById('success_url');
            self.$fail_url = document.getElementById('fail_url');
            self.$partner_id = document.getElementById('partner_id');
            self.$order = document.getElementById('order');
            self.$invoice = document.getElementById('invoice');
            self.$subscription = document.getElementById('subscription');

            if (self.$amount) {
                self.amount = new IMask(self.$amount, {
                    mask: Number,
                    scale: self.$currency.dataset.decimal,
                    signed: false,
                    thousandsSeparator: self.$currency.dataset.thousand,
                    padFractionalZeros: true,
                    normalizeZeros: true,
                    radix: self.$currency.dataset.separator,
                    mapToRadix: [self.$currency.dataset.thousand],
                    min: 0,
                });
                if (self.$amount_installment) {
                    self.amount_installment = new IMask(self.$amount_installment, {
                        mask: Number,
                        scale: self.$currency.dataset.decimal,
                        signed: false,
                        thousandsSeparator: self.$currency.dataset.thousand,
                        padFractionalZeros: true,
                        normalizeZeros: true,
                        radix: self.$currency.dataset.separator,
                        mapToRadix: [self.$currency.dataset.thousand],
                        min: 0,
                    });
                }
                self.cardnumber = new IMask(self.$cardnumber, {
                    mask: [
                        {
                            mask: '0000 000000 00000',
                            regex: '^3[47]\\d{0,13}',
                            cardtype: 'american express'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            regex: '^(?:6011|65\\d{0,2}|64[4-9]\\d?)\\d{0,12}',
                            cardtype: 'discover'
                        },
                        {
                            mask: '0000 000000 0000',
                            regex: '^3(?:0([0-5]|9)|[689]\\d?)\\d{0,11}',
                            cardtype: 'diners'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            regex: '^(5[1-5]\\d{0,2}|22[2-9]\\d{0,1}|2[3-7]\\d{0,2})\\d{0,12}',
                            cardtype: 'mastercard'
                        },
                        {
                            mask: '0000 000000 00000',
                            regex: '^(?:2131|1800)\\d{0,11}',
                            cardtype: 'jcb15'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            regex: '^(?:35\\d{0,2})\\d{0,12}',
                            cardtype: 'jcb'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            regex: '^(?:5[0678]\\d{0,2}|6304|67\\d{0,2})\\d{0,12}',
                            cardtype: 'maestro'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            regex: '^4\\d{0,15}',
                            cardtype: 'visa'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            regex: '^62\\d{0,14}',
                            cardtype: 'unionpay'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            regex: '^(9792|65|36|2205)',
                            cardtype: 'troy'
                        },
                        {
                            mask: '0000 0000 0000 0000',
                            cardtype: 'Unknown'
                        }
                    ],
                    dispatch: function (appended, dynamicMasked) {
                        var number = (dynamicMasked.value + appended).replace(/\D/g, '');

                        for (var i = 0; i < dynamicMasked.compiledMasks.length; i++) {
                            let re = new RegExp(dynamicMasked.compiledMasks[i].regex);
                            if (number.match(re) != null) {
                                return dynamicMasked.compiledMasks[i];
                            }
                        }
                    }
                });
                self.expirationdate = new IMask(self.$expirationdate, {
                    mask: 'MM{/}YY',
                    groups: {
                        YY: new IMask.MaskedPattern.Group.Range([0, 99]),
                        MM: new IMask.MaskedPattern.Group.Range([1, 12]),
                    }
                });
                self.securitycode = new IMask(self.$securitycode, {
                    mask: '0000',
                });

                self.cardnumber.on('accept', self.acceptCardNumber.bind(self));
                self.expirationdate.on('accept', self.acceptExpirationDate.bind(self));
                self.securitycode.on('accept', self.acceptSecurityCode.bind(self));
                self.$amount.addEventListener('change', self.getInstallment.bind(self));
                self.$name.addEventListener('input', self.inputName);
                self.$creditcard.addEventListener('click', self.clickCreditCard.bind(self));
                self.$payment_terms.addEventListener('click', self.clickPaymentTerms.bind(self));
                self.$installments_table.addEventListener('click', self.clickInstallmentTable.bind(self));
                if (self.$payment_pay) {
                    self.$payment_pay.addEventListener('click', self.clickPay.bind(self));
                }
                if (self.$payment_pay0) {
                    self.$payment_pay0.addEventListener('click', self.clickPay.bind(self));
                }
                if (self.$payment_pay1) {
                    self.$payment_pay1.addEventListener('click', self.clickPay.bind(self));
                }
                if (self.$payment_form) {
                    self.$payment_form.addEventListener('click', self.clickPay.bind(self));
                }
                self.$row.addEventListener('click', self.clickRow.bind(self));
                self.$name.addEventListener('focus', self.removeFlipped.bind(self));
                self.$cardnumber.addEventListener('focus', self.removeFlipped.bind(self));
                self.$expirationdate.addEventListener('focus', self.removeFlipped.bind(self));
                self.$securitycode.addEventListener('focus', self.addFlipped.bind(self));
                self._onToggleLoading();
            }
        });
    },

    swapColor: function (color) {
        document.querySelectorAll('.lightcolor').forEach(function (input) {
            input.setAttribute('class', '');
            input.setAttribute('class', 'lightcolor ' + color);
        });
        document.querySelectorAll('.darkcolor').forEach(function (input) {
            input.setAttribute('class', '');
            input.setAttribute('class', 'darkcolor ' + color + 'dark');
        });

        if (color === 'grey') {
            this.$ccicon.classList.remove('show');
        } else {
            this.$ccicon.classList.add('show');
        }
    },

    acceptCardNumber: function () {
        this.getInstallment();
        switch (this.cardnumber.masked.currentMask.cardtype) {
            case 'american express':
                this.$ccicon.innerHTML = cards['amex'];
                this.$ccsingle.innerHTML = cards['amex_single'];
                this.$ccname.value = 'amex';
                this.swapColor('green');
                break;
            case 'visa':
                this.$ccicon.innerHTML = cards['visa'];
                this.$ccsingle.innerHTML = cards['visa_single'];
                this.$ccname.value = 'visa';
                this.swapColor('lime');
                break;
            case 'diners':
                this.$ccicon.innerHTML = cards['diners'];
                this.$ccsingle.innerHTML = cards['diners_single'];
                this.$ccname.value = 'diners';
                this.swapColor('orange');
                break;
            case 'discover':
                this.$ccicon.innerHTML = cards['discover'];
                this.$ccsingle.innerHTML = cards['discover_single'];
                this.$ccname.value = 'discover';
                this.swapColor('purple');
                break;
            case ('jcb' || 'jcb15'):
                this.$ccicon.innerHTML = cards['jcb'];
                this.$ccsingle.innerHTML = cards['jcb_single'];
                this.$ccname.value = 'jcb';
                this.swapColor('red');
                break;
            case 'maestro':
                this.$ccicon.innerHTML = cards['maestro'];
                this.$ccsingle.innerHTML = cards['maestro_single'];
                this.$ccname.value = 'maestro';
                this.swapColor('yellow');
                break;
            case 'mastercard':
                this.$ccicon.innerHTML = cards['mastercard'];
                this.$ccsingle.innerHTML = cards['mastercard_single'];
                this.$ccname.value = 'master';
                this.swapColor('lightblue');
                break;
            case 'troy':
                this.$ccicon.innerHTML = cards['troy'];
                this.$ccsingle.innerHTML = cards['troy_single'];
                this.$ccname.value = 'troy';
                this.swapColor('white');
                break;
            case 'unionpay':
                this.$ccicon.innerHTML = cards['unionpay'];
                this.$ccsingle.innerHTML = cards['unionpay_single'];
                this.$ccname.value = 'unionpay';
                this.swapColor('cyan');
                break;
            default:
                this.$ccicon.innerHTML = '';
                this.$ccsingle.innerHTML = '';
                this.$ccname.value = '';
                this.swapColor('grey');
                break;
        }
    },

    clickCreditCard: function () {
        if (this.$creditcard.classList.contains('flipped')) {
            this.removeFlipped();
        } else {
            this.addFlipped();
        }
    },

    clickPaymentTerms: function (ev) {
        if (ev.target.tagName == 'SPAN' || ev.target.tagName == 'INPUT') {
            return;
        }
        var self = this;
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({
            route: '/payment/card/terms',
            params: {
                partner_id: this.$partner_id && this.$partner_id.value || 0
            }
        }).then(function (content) {
            new dialog(this, {
                title: _t('Terms & Conditions'),
                $content: $(qweb.render('payment_jetcheckout.terms', {content: content})),
            }).open();
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
    },

    clickInstallmentTable: function (ev) {
        var self = this;
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({
            route: '/payment/card/installments',
            params: {
                amount: this.amount.typedValue,
                amount_installment: this.amount_installment && this.amount_installment.typedValue || 0,
                cardnumber: this.cardnumber.typedValue,
            },
        }).then(function (result) {
            if ('error' in result) {
                self.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('An error occured.') + ' ' + result.error,
                });
                return false;
            } else {
                new dialog(this, {
                    title: _t('Installments Table'),
                    $content: result.render
                }).open();
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
    },

    inputName: function () {
        if (this.value.length == 0) {
            document.getElementById('svgname').innerHTML = '';
            document.getElementById('svgnameback').innerHTML = '';
        } else {
            document.getElementById('svgname').innerHTML = this.value;
            document.getElementById('svgnameback').innerHTML = this.value;
        }
    },

    removeFlipped: function () {
        this.$creditcard.classList.remove('flipped');
    },

    addFlipped: function () {
        this.$creditcard.classList.add('flipped');
    },

    clickRow: function (ev) {
        var $rows = $(this.$row).find('div');
        $rows.removeClass('installment-selected');
        $rows.find('input').attr({'checked': false});
        var $el = $(ev.target).closest('div.installment-row');
        $el.addClass('installment-selected');
        $el.find('input').attr({'checked': true});
    },

    acceptExpirationDate: function () {
        if (this.expirationdate.value.length == 0) {
            document.getElementById('svgexpire').innerHTML = '01/23';
        } else {
            document.getElementById('svgexpire').innerHTML = this.expirationdate.value;
        }
    },

    acceptSecurityCode: function () {
        if (this.securitycode.value.length == 0) {
            document.getElementById('svgsecurity').innerHTML = '985';
        } else {
            document.getElementById('svgsecurity').innerHTML = this.securitycode.value;
        }
    },

    getInstallment: function () {
        var self = this;
        if (this.cardnumber.value.length == 0) {
            this.$svgnumber.innerHTML = '0123 4567 8910 1112';
            this.$empty.classList.remove('d-none');
            this.$row.classList.add('d-none');
            this.$row.innerHTML = '';
            this.$cclogo.innerHTML = '';
            this.$cclogo.classList.remove('show');
            this.$ccfamily.value = '';
        } else {
            this.$svgnumber.innerHTML = this.cardnumber.value;
            if (this.cardnumber.typedValue.length >= 6){
                rpc.query({
                    route: '/payment/card/installment',
                    params: {
                        amount: this.amount.typedValue,
                        amount_installment: this.amount_installment && this.amount_installment.typedValue || 0,
                        cardnumber: this.cardnumber.typedValue,
                        prefix: 'bin_',
                        s2s: !(!this.$order && !this.$invoice && !this.$subscription),
                    },
                }).then(function (result) {
                    if ('error' in result) {
                        self.$empty.classList.remove('d-none');
                        self.$row.classList.add('d-none');
                        self.$row.innerHTML = ''
                        self.displayNotification({
                            type: 'warning',
                            title: _t('Warning'),
                            message: _t('An error occured.') + ' ' + result.error,
                        });
                        return false;
                    } else {
                        self.$empty.classList.add('d-none');
                        self.$row.classList.remove('d-none');
                        self.$row.innerHTML = result.render;
                        if (result.card) {
                            self.$cclogo.innerHTML = '<img src="' + result.logo + '" alt="' + result.card + '"/>';
                            self.$cclogo.classList.add('show');
                            self.$ccfamily.value = result.card;
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
            } else {
                this.$empty.classList.remove('d-none');
                this.$row.innerHTML = '';
                this.$cclogo.innerHTML = '';
                this.$cclogo.classList.remove('show');
                this.$ccfamily.value = '';
            }
        }
    },

    format_currency: function(amount, info) {
        const decimals = parseInt(info.data('decimal'));
        const position = info.data('position');
        const symbol = info.data('symbol');
        const amount_formatted = parseFloat(round_di(amount, decimals).toFixed(decimals));
        let currency_formatted = _.str.sprintf('%.' + decimals + 'f', amount_formatted || 0).split('.');
        currency_formatted[0] = utils.insert_thousand_seps(currency_formatted[0]);
        const value = currency_formatted.join(core._t.database.parameters.decimal_point);
        if (position === 'after') {
            return value + ' ' + symbol;
        } else {
            return symbol + ' ' + value;
        }
    },

    checkData: function () {
        if (this.amount.typedValue === '' || this.amount.typedValue === 0) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please enter an amount'),
            });
            return false;
        } else if (this.$name.value === '') {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card holder name'),
            });
            return false;
        } else if (this.cardnumber.typedValue === '') {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card number'),
            });
            return false;
        } else if (this.expirationdate.typedValue === '') {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card expiration date'),
            });
            return false;
        } else if (this.securitycode.typedValue === '') {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please fill card security code'),
            });
            return false;
        } else if (!document.querySelector('input[name="installment_radio"]:checked')) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please select whether payment is straight or installment'),
            });
            return false;
        } else if (!this.$accept_terms.checked) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please accept Terms & Conditions'),
            });
            return false;
        } else {
            return true;
        }
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

    _getParams: function () {
        return {
            installment: document.querySelector('input[name="installment_radio"]:checked').value,
            amount: this.amount.typedValue,
            amount_installment: this.amount_installment && this.amount_installment.typedValue || 0,
            cardnumber: this.cardnumber.typedValue,
            card_holder_name: this.$name.value,
            expire_month: this.expirationdate.typedValue.substring(0,2),
            expire_year: this.expirationdate.typedValue.substring(3),
            cvc: this.securitycode.typedValue,
            card_type: this.$ccname.value,
            card_family: this.$ccfamily.value,
            success_url: this.$success_url && this.$success_url.value || false,
            fail_url: this.$fail_url && this.$fail_url.value || false,
            partner_id: this.$partner_id && this.$partner_id.value || 0,
            order: this.$order && this.$order.value || 0,
            invoice: this.$invoice && this.$invoice.value || 0,
            subscription: this.$subscription && this.$subscription.value || 0,
        }
    },
    
    clickPay: function () {
        var self = this;
        if (this.checkData()) {
            self._onToggleLoading(true);
            rpc.query({
                route: '/payment/card/payment',
                params: this._getParams(),
            }).then(function (result) {
                if ('error' in result) {
                    self.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: _t('An error occured.') + ' ' + result.error,
                    });
                    self._onToggleLoading();
                } else {
                    window.location = result.redirect_url;
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
                self._onToggleLoading();
            });
        }
    },
});

publicWidget.registry.JetcheckoutPaymentTransaction = publicWidget.Widget.extend({
    selector: '.payment-transaction',

    start: function () {
        return this._super.apply(this, arguments).then(function () {
            $(".table-fold tr.row-view").on("click", function(){
                $(this).toggleClass("open").next(".row-fold").toggleClass("open");
            });
        });
    },
});

});