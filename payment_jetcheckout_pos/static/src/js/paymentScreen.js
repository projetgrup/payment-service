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
            this.vpos_card_bin = 0;
            this.vpos_amount = 0;
            this.vpos_partner = 0;
        }

        mounted() {
            this.$cctype = '';
            this.$ccfamily = '';
            this.$ccname = document.getElementById('ccname');
            this.$ccnumber = document.getElementById('ccnumber');
            this.$ccexpiry = document.getElementById('ccexpiry');
            this.$ccsecurity = document.getElementById('ccsecurity');
            this.$ccicon = document.getElementById('ccicon');
            this.$cclogo = document.getElementById('cclogo');
            this.$rows = document.getElementById('installment_rows');
            this.$empty = document.getElementById('installment_empty');
            this.$loading = document.getElementById('installment_loading');
            
            this.vpos_ccnumber = new IMask(this.$ccnumber, {
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

            this.vpos_expiry = new IMask(this.$ccexpiry, {
                mask: 'MM{/}YY',
                groups: {
                    YY: new IMask.MaskedPattern.Group.Range([0, 99]),
                    MM: new IMask.MaskedPattern.Group.Range([1, 12]),
                }
            });

            this.vpos_security = new IMask(this.$ccsecurity, {
                mask: '000[0]',
            });

            this.vpos_ccnumber.on('accept', this.onAcceptCardNumber.bind(this));
            this.$rows.addEventListener('click', this.onClickRow.bind(this));
            this.env.pos.on('change:selectedClient', () => this.getInstallment(), this);
            this.currentOrder.paymentlines.on('add remove change', () => this.getInstallment(), this);
            this.getInstallment();
        }

        async showInstallments() {
            await this.showPopup('InstallmentPopup', {
                title: this.env._t('Installment Table'),
                acquirer: this.vpos_acquirer,
                amount: this.vpos_amount,
            });
        }

        getInstallment() {
            const order = this.currentOrder;
            const client = order.get_client();
            const cardnumber = this.vpos_ccnumber.typedValue;
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
                this.$empty.classList.remove('d-none');
                this.$rows.classList.add('d-none');
                this.$rows.innerHTML = '';
                this.$cclogo.innerHTML = '';
                this.$cclogo.classList.remove('show');
                this.$ccfamily = '';
            } else {
                try {
                    const self = this;
                    $(this.$loading).addClass('visible');
                    this.env.session.rpc('/payment/card/installment', {
                        amount: amount,
                        partner: partner,
                        cardnumber: this.vpos_ccnumber.typedValue,
                        prefix: 'bin_',
                        render: true,
                        s2s: true,
                    }).then(function (result) {
                        if ('error' in result) {
                            self.$empty.classList.remove('d-none');
                            self.$rows.classList.add('d-none');
                            self.$rows.innerHTML = '';
                            self.showPopup('ErrorPopup', {
                                title: self.env._t('Error'),
                                body: self.env._t('An error occured.') + ' ' + result.error,
                            });
                        } else {
                            self.$empty.classList.add('d-none');
                            self.$rows.classList.remove('d-none');
                            self.$rows.innerHTML = result.render;
                            if (result.card) {
                                self.$cclogo.innerHTML = '<img src="' + result.logo + '" alt="' + result.card + '"/>';
                                self.$cclogo.classList.add('show');
                                self.$ccfamily = result.card;
                            }
                        }
                        $(self.$loading).removeClass('visible');
                    });
                } catch(error) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('An error occured. Please contact with your system administrator.'),
                    });
                    console.log(error);
                    $(this.$loading).removeClass('visible');
                }
            }
        }

        onAcceptCardNumber() {
            this.getInstallment();
            let type = '';
            let code = '';
            switch (this.vpos_ccnumber.masked.currentMask.cardtype) {
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

            this.$cctype = type;
            if (code) {
                this.$ccicon.innerHTML = Cards[code];
                this.$ccicon.classList.add('show');
            } else {
                this.$ccicon.innerHTML = '';
                this.$ccicon.classList.remove('show');
            }
        }

        onClickRow(ev) {
            var $rows = $(this.$rows).find('div');
            $rows.removeClass('installment-selected');
            $rows.find('input').attr({'checked': false});
            var $el = $(ev.target).closest('div.installment-row');
            $el.addClass('installment-selected');
            $el.find('input').attr({'checked': true});
        }
    };

Registries.Component.extend(PaymentScreen, JetcheckoutPaymentScreen)