/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';
import Cards from 'payment_jetcheckout.cards';

export const JetcheckoutPaymentScreen = (PaymentScreen) => 
    class JetcheckoutPaymentScreen extends PaymentScreen {
        constructor() {
            super(...arguments);
            this.jetcheckout = this.env.pos.jetcheckout;
            this.$jetcheckout = {}
            this.$$jetcheckout = {}

            this.jetcheckout_payments = {}
            this.jetcheckout_paid = false;
            this.jetcheckout_card_bin = 0;
            this.jetcheckout_amount = 0;
            this.jetcheckout_partner = 0;
        }

        mounted() {
            this.$jetcheckout = {
                card: {
                    type: '',
                    family: '',
                    holder: document.getElementById('jetcheckout_card_holder'),
                    number: document.getElementById('jetcheckout_card_number'),
                    security: document.getElementById('jetcheckout_card_security'),
                    expiry: document.getElementById('jetcheckout_card_expiry'),
                    icon: document.getElementById('jetcheckout_card_icon'),
                    logo: document.getElementById('jetcheckout_card_logo'),
                    threed: document.getElementById('jetcheckout_card_threed'),
                    result: document.getElementById('jetcheckout_card_result'),
                },
                installment: {
                    rows: document.getElementById('jetcheckout_installment_rows'),
                    empty: document.getElementById('jetcheckout_installment_empty'),
                    loading: document.getElementById('jetcheckout_installment_loading'),
                },
                payment: {
                    loading: document.getElementById('jetcheckout_payment_loading'),
                    threed: document.getElementById('jetcheckout_payment_threed'),
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
            this.$jetcheckout.card.number.addEventListener('change', this._onChangeResult.bind(this));
            this.env.pos.on('change:selectedClient', () => this.getCardInstallment(), this);
            this.currentOrder.paymentlines.on('add remove change', () => this.getCardInstallment(), this);
            //this.getCardInstallment();
        }

        _enablePayButton() {
            $('.button.next').removeClass('disabled');
        }

        _disablePayButton() {
            $('.button.next').addClass('disabled');
        }

        _onChangeResult(ev) {
            const value = ev.target.value.replaceAll('&#34;','"');
            const result = JSON.parse(value);
            if (result.state === 'done') {
                this.jetcheckout_paid = true;
                this._finalizeValidation();
            } else {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: result.message || this.env._t('An error occured. Please try again.') ,
                });
            }

            this.currentOrder.transaction_ids.push(result.id)
            this.$jetcheckout.payment.loading.classList.remove('visible-half');
            this.$jetcheckout.payment.threed.classList.remove('visible');
            this._enablePayButton();
        }

        async _finalizeValidation() {
            if (!this.jetcheckout_paid && this.jetcheckout_amount > 0) {
                this._disablePayButton();
                this._onCardPay();
                return;
            }
            await super._finalizeValidation();
        }

        async showCardInstallments() {
            await this.showPopup('InstallmentPopup', {
                title: this.env._t('Installment Table'),
                acquirer: this.jetcheckout_acquirer,
                amount: this.jetcheckout_amount,
            });
        }

        getCardInstallment() {
            const order = this.currentOrder;
            const client = order.get_client();
            const cardnumber = this.$$jetcheckout.number.typedValue;
            console.log(this.paymentLines);
            const paymentLine = _.find(this.paymentLines, function(line) {
                return line.payment_method.is_jetcheckout;
            });

            const amount = paymentLine && paymentLine.amount || 0;
            const partner = client && client.id || 0;
            const cardBin = cardnumber.length  && parseInt(cardnumber.toString().substring(0,6)) || 0;
            if (this.jetcheckout_card_bin === cardBin && this.jetcheckout_amount === amount && this.jetcheckout_partner === partner) return;
            this.jetcheckout_amount = amount;
            this.jetcheckout_partner = partner;
            this.jetcheckout_card_bin = cardBin;
            if (this.jetcheckout_amount <= 0) return;

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
                        amount: amount,
                        amount_installment: 0,
                        partner: partner,
                        cardnumber: this.$$jetcheckout.number.typedValue,
                        prefix: 'bin_',
                        render: true,
                        s2s: true,
                    }).then(function (result) {
                        if ('error' in result) {
                            self.$jetcheckout.installment.empty.classList.remove('d-none');
                            self.$jetcheckout.installment.rows.classList.add('d-none');
                            self.$jetcheckout.installment.rows.innerHTML = '';
                            self.showPopup('ErrorPopup', {
                                title: self.env._t('Error'),
                                body: self.env._t('An error occured.') + ' ' + result.error,
                            });
                        } else {
                            self.$jetcheckout.installment_empty.classList.add('d-none');
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
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('An error occured. Please contact with your system administrator.'),
                    });
                    console.error(error);
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

        closeCardThreed() {
            this.$jetcheckout.payment.threed.classList.remove('visible');
            this.$jetcheckout.payment.loading.classList.remove('visible-half');
            this._enablePayButton();
        }

        _checkCardData() {
            if (!(this.jetcheckout_partner > 0)) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please select a customer'),
                });
                return false;
            } else if (!(this.jetcheckout_amount > 0)) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please enter an amount'),
                });
                return false;
            } else if (this.$jetcheckout.card.name.value === '') {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please fill card holder name'),
                });
                return false;
            } else if (this.$$jetcheckout.number.typedValue === '') {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please fill card number'),
                });
                return false;
            } else if (this.$$jetcheckout.typedValue === '') {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please fill card expiration date'),
                });
                return false;
            } else if (this.$$jetcheckout.security.typedValue === '') {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please fill card security code'),
                });
                return false;
            } else if (!document.querySelector('input[name="installment_radio"]:checked')) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please select whether payment is straight or installment'),
                });
                return false;
            } else {
                return true;
            }
        }

        _getCardParams() {
            return {
                installment: document.querySelector('input[name="installment_radio"]:checked').value,
                installment_desc: document.querySelector('input[name="installment_radio"]:checked').dataset.value,
                amount: this.jetcheckout_amount,
                amount_installment: 0,
                partner: this.jetcheckout_partner,
                cardnumber: this.$$jetcheckout.number.typedValue,
                card_holder_name: this.$jetcheckout.card.name.value,
                expire_month: this.$$jetcheckout.expiry.typedValue.substring(0,2),
                expire_year: this.$$jetcheckout.expiry.typedValue.substring(3),
                cvc: this.$$jetcheckout.security.typedValue,
                card_type: this.$jetcheckout.card.type,
                card_family: this.$jetcheckout.card.family,
                success_url: '/pos/card/success',
                fail_url: '/pos/card/fail',
            }
        }
        
        _onCardPay() {
            const self = this;
            if (this._checkCardData()) {
                try {
                    this.$jetcheckout.payment.loading.classList.add('visible-half');
                    this.env.session.rpc('/payment/card/payment', this._getCardParams()).then(function (result) {
                        if ('url' in result) {
                            self.$jetcheckout.card.threed.src = result.url;
                            self.$jetcheckout.payment.threed.classList.add('visible');
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
                    this._enablePayButton();
                    console.error(error);
                    this.$jetcheckout.payment.loading.classList.remove('visible-half');
                }
            } else {
                this._enablePayButton();
            }
        }
    };

Registries.Component.extend(PaymentScreen, JetcheckoutPaymentScreen)