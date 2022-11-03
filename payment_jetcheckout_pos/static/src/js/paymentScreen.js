/** @odoo-module **/

import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';
import Cards from 'payment_jetcheckout.cards';

export const JetcheckoutPaymentScreen = (PaymentScreen) => 
    class JetcheckoutPaymentScreen extends PaymentScreen {
        constructor() {
            super(...arguments);
            this.vpos_acquirer = this.env.pos.vpos_acquirer;
            this.vpos_card_types = this.env.pos.vpos_card_types;
            this.vpos_card_families = this.env.pos.vpos_card_families;
            this.vpos_paid = false;
            this.vpos_card_bin = 0;
            this.vpos_amount = 0;
            this.vpos_partner = 0;
        }

        mounted() {
            this.$vpos_card_type = '';
            this.$vpos_card_family = '';
            this.$vpos_card_name = document.getElementById('vpos_card_name');
            this.$vpos_card_number = document.getElementById('vpos_card_number');
            this.$vpos_card_expiry = document.getElementById('vpos_card_expiry');
            this.$vpos_card_security = document.getElementById('vpos_card_security');
            this.$vpos_card_icon = document.getElementById('vpos_card_icon');
            this.$vpos_card_logo = document.getElementById('vpos_card_logo');
            this.$vpos_card_threed = document.getElementById('vpos_card_threed');
            this.$vpos_card_result = document.getElementById('vpos_card_result');
            this.$vpos_installment_rows = document.getElementById('vpos_installment_rows');
            this.$vpos_installment_empty = document.getElementById('vpos_installment_empty');
            this.$vpos_installment_loading = document.getElementById('vpos_installment_loading');
            this.$vpos_payment_loading = document.getElementById('vpos_payment_loading');
            this.$vpos_payment_threed = document.getElementById('vpos_payment_threed');
            
            this.vpos_card_number = new IMask(this.$vpos_card_number, {
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

            this.vpos_card_expiry = new IMask(this.$vpos_card_expiry, {
                mask: 'MM{/}YY',
                groups: {
                    YY: new IMask.MaskedPattern.Group.Range([0, 99]),
                    MM: new IMask.MaskedPattern.Group.Range([1, 12]),
                }
            });

            this.vpos_card_security = new IMask(this.$vpos_card_security, {
                mask: '000[0]',
            });

            this.vpos_card_number.on('accept', this.onAcceptCardNumber.bind(this));
            this.$vpos_installment_rows.addEventListener('click', this.onClickCardInstallment.bind(this));
            this.$vpos_card_result.addEventListener('change', this._onChangeResult.bind(this));
            this.env.pos.on('change:selectedClient', () => this.getCardInstallment(), this);
            this.currentOrder.paymentlines.on('add remove change', () => this.getCardInstallment(), this);
            this.getCardInstallment();
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
                this.vpos_paid = true;
                this._finalizeValidation();
            } else {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: result.message || this.env._t('An error occured. Please try again.') ,
                });
            }

            this.currentOrder.transaction_ids.push(result.id)
            this.$vpos_payment_loading.classList.remove('visible-half');
            this.$vpos_payment_threed.classList.remove('visible');
            this._enablePayButton();
        }

        async _finalizeValidation() {
            if (!this.vpos_paid && this.vpos_amount > 0) {
                this._disablePayButton();
                this._onCardPay();
                return;
            }
            await super._finalizeValidation();
        }

        async showCardInstallments() {
            await this.showPopup('InstallmentPopup', {
                title: this.env._t('Installment Table'),
                acquirer: this.vpos_acquirer,
                amount: this.vpos_amount,
            });
        }

        getCardInstallment() {
            const order = this.currentOrder;
            const client = order.get_client();
            const cardnumber = this.vpos_card_number.typedValue;
            const paymentLine = _.find(this.paymentLines, function(line) {
                return line.payment_method.is_vpos;
            });

            const amount = paymentLine && paymentLine.amount || 0;
            const partner = client && client.id || 0;
            const cardBin = cardnumber.length  && parseInt(cardnumber.toString().substring(0,6)) || 0;
            if (this.vpos_card_bin === cardBin && this.vpos_amount === amount && this.vpos_partner === partner) return;
            this.vpos_amount = amount;
            this.vpos_partner = partner;
            this.vpos_card_bin = cardBin;
            if (this.vpos_amount <= 0) return;

            if (cardnumber.length < 6) {
                this.$vpos_installment_empty.classList.remove('d-none');
                this.$vpos_installment_rows.classList.add('d-none');
                this.$vpos_installment_rows.innerHTML = '';
                this.$vpos_card_logo.innerHTML = '';
                this.$vpos_card_logo.classList.remove('show');
                this.$vpos_card_family = '';
            } else {
                try {
                    const self = this;
                    $(this.$vpos_installment_loading).addClass('visible');
                    this.env.session.rpc('/payment/card/installment', {
                        amount: amount,
                        amount_installment: 0,
                        partner: partner,
                        cardnumber: this.vpos_card_number.typedValue,
                        prefix: 'bin_',
                        render: true,
                        s2s: true,
                    }).then(function (result) {
                        if ('error' in result) {
                            self.$vpos_installment_empty.classList.remove('d-none');
                            self.$vpos_installment_rows.classList.add('d-none');
                            self.$vpos_installment_rows.innerHTML = '';
                            self.showPopup('ErrorPopup', {
                                title: self.env._t('Error'),
                                body: self.env._t('An error occured.') + ' ' + result.error,
                            });
                        } else {
                            self.$vpos_installment_empty.classList.add('d-none');
                            self.$vpos_installment_rows.classList.remove('d-none');
                            self.$vpos_installment_rows.innerHTML = result.render;
                            if (result.card) {
                                self.$vpos_card_logo.innerHTML = '<img src="' + result.logo + '" alt="' + result.card + '"/>';
                                self.$vpos_card_logo.classList.add('show');
                                self.$vpos_card_family = result.card;
                            }
                        }
                        $(self.$vpos_installment_loading).removeClass('visible');
                    });
                } catch(error) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('An error occured. Please contact with your system administrator.'),
                    });
                    console.error(error);
                    $(this.$vpos_installment_loading).removeClass('visible');
                }
            }
        }

        onAcceptCardNumber() {
            this.getCardInstallment();
            let type = '';
            let code = '';
            switch (this.vpos_card_number.masked.currentMask.cardtype) {
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

            this.$vpos_card_type = type;
            if (code) {
                this.$vpos_card_icon.innerHTML = Cards[code];
                this.$vpos_card_icon.classList.add('show');
            } else {
                this.$vpos_card_icon.innerHTML = '';
                this.$vpos_card_icon.classList.remove('show');
            }
        }

        onClickCardInstallment(ev) {
            let $rows = $(this.$vpos_installment_rows).find('div');
            $rows.removeClass('installment-selected');
            $rows.find('input').attr({'checked': false});
            let $el = $(ev.target).closest('div.installment-row');
            $el.addClass('installment-selected');
            $el.find('input').attr({'checked': true});
        }

        closeCardThreed() {
            this.$vpos_payment_threed.classList.remove('visible');
            this.$vpos_payment_loading.classList.remove('visible-half');
            this._enablePayButton();
        }

        _checkCardData() {
            if (!(this.vpos_partner > 0)) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please select a customer'),
                });
                return false;
            } else if (!(this.vpos_amount > 0)) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please enter an amount'),
                });
                return false;
            } else if (this.$vpos_card_name.value === '') {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please fill card holder name'),
                });
                return false;
            } else if (this.vpos_card_number.typedValue === '') {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please fill card number'),
                });
                return false;
            } else if (this.vpos_card_expiry.typedValue === '') {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('Please fill card expiration date'),
                });
                return false;
            } else if (this.vpos_card_security.typedValue === '') {
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
                amount: this.vpos_amount,
                amount_installment: 0,
                partner: this.vpos_partner,
                cardnumber: this.vpos_card_number.typedValue,
                card_holder_name: this.$vpos_card_name.value,
                expire_month: this.vpos_card_expiry.typedValue.substring(0,2),
                expire_year: this.vpos_card_expiry.typedValue.substring(3),
                cvc: this.vpos_card_security.typedValue,
                card_type: this.$vpos_card_type,
                card_family: this.$vpos_card_family,
                success_url: '/pos/card/success',
                fail_url: '/pos/card/fail',
            }
        }
        
        _onCardPay() {
            const self = this;
            if (this._checkCardData()) {
                try {
                    this.$vpos_payment_loading.classList.add('visible-half');
                    this.env.session.rpc('/payment/card/payment', this._getCardParams()).then(function (result) {
                        if ('url' in result) {
                            self.$vpos_card_threed.src = result.url;
                            self.$vpos_payment_threed.classList.add('visible');
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
                    this.$vpos_payment_loading.classList.remove('visible-half');
                }
            } else {
                this._enablePayButton();
            }
        }
    };

Registries.Component.extend(PaymentScreen, JetcheckoutPaymentScreen)