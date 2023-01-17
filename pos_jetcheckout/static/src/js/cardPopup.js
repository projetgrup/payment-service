odoo.define('pos_jetcheckout.CardPopup', function(require) {
'use strict';

const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
const Registries = require('point_of_sale.Registries');
const Cards = require('payment_jetcheckout.cards');
var core = require('web.core');

var _t = core._t;

class JetcheckoutCardPopup extends AbstractAwaitablePopup {
    constructor() {
        super(...arguments);
        this.order = this.props.order;
        this.line = this.props.line;
        this.amount = this.props.amount;
        this.partner = this.props.partner;
        this.inPayment = false;
        this.jetcheckout = this.env.pos.jetcheckout;
        this.$jetcheckout = {};
        this.$$jetcheckout = {};
    }

    showPopup(name, props) {
        if (name === 'ErrorPopup') {
            this.line.set_payment_status('retry');
        }
        return super.showPopup(...arguments);
    }

    showNotificationSuccess(message) {
        const duration = 2001;
        this.trigger('show-notification', { message, duration });
    }

    showNotificationDanger(message) {
        const duration = 2002;
        this.trigger('show-notification', { message, duration });
    }

    mounted() {
        this.$jetcheckout = {
            card: {
                type: '',
                family: '',
                bin: '',
                holder: document.getElementById('jetcheckout_card_holder'),
                number: document.getElementById('jetcheckout_card_number'),
                security: document.getElementById('jetcheckout_card_security'),
                expiry: document.getElementById('jetcheckout_card_expiry'),
                icon: document.getElementById('jetcheckout_card_icon'),
                logo: document.getElementById('jetcheckout_card_logo'),
            },
            installment: {
                rows: document.getElementById('jetcheckout_installment_rows'),
                empty: document.getElementById('jetcheckout_installment_empty'),
                loading: document.getElementById('jetcheckout_installment_loading'),
            },
            payment: {
                //loading: document.getElementById('jetcheckout_payment_loading'),
                threed: document.getElementById('jetcheckout_payment_threed'),
                url: document.getElementById('jetcheckout_payment_url'),
                result: document.getElementById('jetcheckout_payment_result'),
            }
        }

        this.$$jetcheckout.number = new IMask(this.$jetcheckout.card.number, {
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
                let number = (dynamicMasked.value + appended).replace(/\D/g, '');
                for (let i = 0; i < dynamicMasked.compiledMasks.length; i++) {
                    let re = new RegExp(dynamicMasked.compiledMasks[i].regex);
                    if (number.match(re) != null) {
                        return dynamicMasked.compiledMasks[i];
                    }
                }
            }
        });

        this.$$jetcheckout.expiry = new IMask(this.$jetcheckout.card.expiry, {
            mask: 'MM{/}YY',
            groups: {
                YY: new IMask.MaskedPattern.Group.Range([0, 99]),
                MM: new IMask.MaskedPattern.Group.Range([1, 12]),
            }
        });

        this.$$jetcheckout.security = new IMask(this.$jetcheckout.card.security, {
            mask: '000[0]',
        });

        this.$$jetcheckout.number.on('accept', this.onAcceptCardNumber.bind(this));
        this.$jetcheckout.installment.rows.addEventListener('click', this.onClickCardInstallment.bind(this));
        this.$jetcheckout.payment.result.addEventListener('change', this._onChangeResult.bind(this));
    }

    _onChangeResult(ev) {
        const value = ev.target.value.replaceAll('&#34;','"');
        const result = JSON.parse(value);
        if (result.state === 'done') {
            this.line.set_payment_status('done');
            this.order.transaction_ids.push(result.id);
            this.trigger('close-popup');
        } else {
            this.showPopup('ErrorPopup', {
                title: this.env._t('Error'),
                body: result.message || this.env._t('An error occured. Please try again.'),
            });
        }
    }

    getCardInstallment() {
        const cardnumber = this.$$jetcheckout.number.typedValue;
        const cardBin = cardnumber.length  && parseInt(cardnumber.toString().substring(0,6)) || 0;
        if (this.$jetcheckout.card.bin === cardBin) return;
        this.$jetcheckout.card.bin = cardBin;

        if (cardnumber.length < 6) {
            this.$jetcheckout.installment.empty.classList.remove('d-none');
            this.$jetcheckout.installment.rows.classList.add('d-none');
            this.$jetcheckout.installment.rows.innerHTML = '';
            this.$jetcheckout.card.logo.innerHTML = '';
            this.$jetcheckout.card.logo.classList.remove('show');
            this.$jetcheckout.card.family = '';
        } else {
            try {
                const self = this;
                $(this.$jetcheckout.installment.loading).addClass('visible');
                this.env.session.rpc('/payment/card/installment', {
                    amount: this.amount,
                    amount_installment: 0,
                    partner: this.partner,
                    cardnumber: this.$$jetcheckout.number.typedValue,
                    prefix: 'bin_',
                    render: true,
                    s2s: true,
                }).then(function (result) {
                    if ('error' in result) {
                        self.$jetcheckout.installment.empty.classList.remove('d-none');
                        self.$jetcheckout.installment.rows.classList.add('d-none');
                        self.$jetcheckout.installment.rows.innerHTML = '';
                        self.showNotificationDanger(self.env._t('An error occured.') + ' ' + result.error);
                    } else {
                        self.$jetcheckout.installment.empty.classList.add('d-none');
                        self.$jetcheckout.installment.rows.classList.remove('d-none');
                        self.$jetcheckout.installment.rows.innerHTML = result.render;
                        if (result.card) {
                            self.$jetcheckout.card.logo.innerHTML = '<img src="' + result.logo + '" alt="' + result.card + '"/>';
                            self.$jetcheckout.card.logo.classList.add('show');
                            self.$jetcheckout.card.family = result.card;
                        }
                    }
                    $(self.$jetcheckout.installment.loading).removeClass('visible');
                });
            } catch(error) {
                console.error(error);
                this.showNotificationDanger(this.env._t('An error occured. Please contact with your system administrator.'));
                $(this.$jetcheckout.installment.loading).removeClass('visible');
            }
        }
    }

    onAcceptCardNumber() {
        this.getCardInstallment();

        let type = '';
        let code = '';
        switch (this.$$jetcheckout.number.masked.currentMask.cardtype) {
            case 'american express':
                type = 'American Express';
                code = 'amex';
                break;
            case 'visa':
                type = 'Visa';
                code = 'visa';
                break;
            case 'diners':
                type = 'Diners';
                code = 'diners';
                break;
            case 'discover':
                type = 'Discover';
                code = 'discover';
                break;
            case ('jcb' || 'jcb15'):
                type = 'JCB';
                code = 'jcb';
                break;
            case 'maestro':
                type = 'Maestro';
                code = 'maestro';
                break;
            case 'mastercard':
                type = 'Mastercard';
                code = 'mastercard';
                break;
            case 'troy':
                type = 'Troy';
                code = 'troy';
                break;
            case 'unionpay':
                type = 'UnionPay';
                code = 'unionpay';
                break;
            default:
                type = '';
                code = '';
                break;
        }

        this.$jetcheckout.card.type = type;
        if (code) {
            this.$jetcheckout.card.icon.innerHTML = Cards[code];
            this.$jetcheckout.card.icon.classList.add('show');
        } else {
            this.$jetcheckout.card.icon.innerHTML = '';
            this.$jetcheckout.card.icon.classList.remove('show');
        }
    }

    onClickCardInstallment(ev) {
        let $rows = $(this.$jetcheckout.installment.rows).find('div');
        $rows.removeClass('installment-selected');
        $rows.find('input').attr({'checked': false});
        let $el = $(ev.target).closest('div.installment-row');
        $el.addClass('installment-selected');
        $el.find('input').attr({'checked': true});
    }

    _checkCardData() {
        if (!(this.partner > 0)) {
            this.showNotificationDanger(this.env._t('Please select a customer'));
            return false;
        } else if (this.$jetcheckout.card.holder.value === '') {
            this.showNotificationDanger(this.env._t('Please fill card holder name'));
            return false;
        } else if (this.$$jetcheckout.number.typedValue === '') {
            this.showNotificationDanger(this.env._t('Please fill card number'));
            return false;
        } else if (this.$$jetcheckout.typedValue === '') {
            this.showNotificationDanger(this.env._t('Please fill card expiration date'));
            return false;
        } else if (this.$$jetcheckout.security.typedValue === '') {
            this.showNotificationDanger(this.env._t('Please fill card security code'));
            return false;
        } else if (!document.querySelector('input[name="installment_radio"]:checked')) {
            this.showNotificationDanger(this.env._t('Please select whether payment is straight or installment'));
            return false;
        } else {
            return true;
        }
    }

    _getCardParams() {
        return {
            installment: document.querySelector('input[name="installment_radio"]:checked').value,
            installment_desc: document.querySelector('input[name="installment_radio"]:checked').dataset.value,
            amount: this.amount,
            amount_installment: 0,
            partner: this.partner,
            cardnumber: this.$$jetcheckout.number.typedValue,
            card_holder_name: this.$jetcheckout.card.holder.value,
            expire_month: this.$$jetcheckout.expiry.typedValue.substring(0,2),
            expire_year: this.$$jetcheckout.expiry.typedValue.substring(3),
            cvc: this.$$jetcheckout.security.typedValue,
            card_type: this.$jetcheckout.card.type,
            card_family: this.$jetcheckout.card.family,
            success_url: '/pos/card/success',
            fail_url: '/pos/card/fail',
        }
    }
    
    pay() {
        const self = this;
        $('div.button.pay').addClass('disabled');
        if (this._checkCardData()) {
            try {
                this.inPayment = true;
                $('div.button.pay').addClass('d-none');
                $('.payment-jetcheckout').fadeOut(function () {
                    $('div.jetcheckout-popup main').css('height', '400px');
                    self.$jetcheckout.payment.threed.classList.add('d-block');
                });
                this.env.session.rpc('/payment/card/payment', this._getCardParams()).then(function (result) {
                    if ('url' in result) {
                        self.$jetcheckout.payment.url.src = result.url;
                    } else {
                        self.showPopup('ErrorPopup', {
                            title: self.env._t('Error'),
                            body: self.env._t('An error occured.') + ' ' + result.error,
                        });
                    }
                });
            } catch(error) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('An error occured. Please contact with your system administrator.'),
                });
                console.error(error);
            }
        } else {
            $('div.button.pay').removeClass('d-none');
            $('div.button.pay').removeClass('disabled');
        }
    }
}

JetcheckoutCardPopup.template = 'JetcheckoutCardPopup';
JetcheckoutCardPopup.defaultProps = {
    title: _t('Card Information'),
};

Registries.Component.add(JetcheckoutCardPopup);

return JetcheckoutCardPopup;
});
