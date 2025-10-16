/** @odoo-module alias=paylox.system.escrow.broker **/
'use strict';

import rpc from 'web.rpc';
import { _t } from 'web.core';
import publicWidget from 'web.public.widget';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';

const REGEXP_EMAIL = /^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$/;

publicWidget.registry.payloxBrokerRegistration = payloxPage.extend({
    selector: '.broker-registration #wrapwrap',
    jsLibs: [
        '/payment_jetcheckout/static/src/lib/imask/imask.js',
        '/payment_jetcheckout/static/src/lib/filepond/filepond.js',
    ],

    init: function (parent, options) {
        this._super(parent, options);
        this.filePonds = {};
        this.partner = 0;
        this.phoneVerified = false;
        this.otpTimer = null;
        this.otpId = null;
        
        this.broker = {
            button: {
                next: new fields.element({
                    events: [['click', this._onClickNext]]
                }),
                back: new fields.element({
                    events: [['click', this._onClickBack]]
                }),
                submit: new fields.element({
                    events: [['click', this._onClickSubmit]]
                }),
                otpSubmit: new fields.element({
                    events: [['click', this._onClickOtpSubmit]]
                }),
                otpCancel: new fields.element({
                    events: [['click', this._onClickOtpCancel]]
                }),
                otpResend: new fields.element({
                    events: [['click', this._onClickOtpResend]]
                }),
            },
            input: {
                vat: new fields.element({
                    mask: '00000000000',
                    validate: () => {
                        const field = this.broker.input.vat;
                        let message = null;
                        let valid = true;
                        if (!field._.masked.isComplete) {
                            message = _t('TC Identity Number is required');
                            valid = false;
                        } else if (!this._isTcknValid(field.value)) {
                            message = _t('Tax ID is not valid');
                            valid = false;
                        } 
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                tax_number: new fields.string({
                    mask: '00000000000',
                    validate: () => {
                        const field = this.broker.input.tax_number;
                        let message = null;
                        let valid = true;
                        if (!field._.masked.isComplete) {
                            message = _t('Tax ID is required');
                            valid = false;
                        }else if (!this._isVatValid(field.value)) {
                            message = _t('Tax ID is not valid');
                            valid = false;
                        } 
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                name: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const field = this.broker.input.name;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Name is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                company_title: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ0-9]+[A-Za-zığüşöçĞÜŞÖÇİ0-9\s]*$/,
                    validate: () => {
                        const field = this.broker.input.company_title;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Company title is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                sign_name: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ0-9]+[A-Za-zığüşöçĞÜŞÖÇİ0-9\s]*$/,
                    validate: () => {
                        const field = this.broker.input.sign_name;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Sign name is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                state: new fields.element({
                    validate: () => {
                        const field = this.broker.input.state;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('City is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                city: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const field = this.broker.input.city;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('District is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                person: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const field = this.broker.input.person;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Authorized person is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                phone: new fields.string({
                    mask: '000 000 0000',
                    events: [['input', () => this._onPhoneInput()]],
                    validate: () => {
                        const field = this.broker.input.phone;
                        let message = null;
                        let valid = true;
                        
                        if (!field._.masked.isComplete) {
                            message = _t('Phone number is required');
                            valid = false;
                        }
                        
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                email: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const field = this.broker.input.email;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Email is required');
                            valid = false;
                        } else if (!REGEXP_EMAIL.test(field.value)) {
                            message = _t('Email format is not correct');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                iban: new fields.string({
                    mask: 'TR00 0000 0000 0000 0000 0000 00',
                    validate: () => {
                        const field = this.broker.input.iban;
                        let message = null;
                        let valid = true;
                        if (!field._.masked.isComplete) {
                            message = _t('IBAN is required');
                            valid = false;
                        } else if (!this._isIbanValid(field._.masked.value)) {
                            message = _t('IBAN is not valid');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                iban_name: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ0-9]+[A-Za-zığüşöçĞÜŞÖÇİ0-9\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const field = this.broker.input.iban_name;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Account holder name is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                fileTaxPlate: new fields.file({
                    name: 'fileTaxPlate',
                    allowMultiple: false,
                    accept: 'image/png, image/jpeg, image/gif, application/pdf',
                    maxFileSize: '10MB',
                    labelIdle: 'Drag & Drop your file or <span class="filepond--label-action">Browse</span>',
                    validate: () => {
                        const field = this.broker.input.fileTaxPlate;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Tax Plate is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                fileSignatureCircular: new fields.file({
                    name: 'fileSignatureCircular',
                    allowMultiple: false,
                    accept: 'image/png, image/jpeg, image/gif, application/pdf',
                    maxFileSize: '10MB',
                    labelIdle: 'Drag & Drop your file or <span class="filepond--label-action">Browse</span>',
                    validate: () => {
                        const field = this.broker.input.fileSignatureCircular;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Signature Circular is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                fileIdentity: new fields.file({
                    name: 'fileIdentity',
                    allowMultiple: false,
                    accept: 'image/png, image/jpeg, image/gif, application/pdf',
                    maxFileSize: '10MB',
                    labelIdle: 'Drag & Drop your file or <span class="filepond--label-action">Browse</span>',
                    validate: () => {
                        const field = this.broker.input.fileIdentity;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Identity Document is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                fileAuthorization: new fields.file({
                    name: 'fileAuthorization',
                    allowMultiple: false,
                    accept: 'image/png, image/jpeg, image/gif, application/pdf',
                    maxFileSize: '10MB',
                    labelIdle: 'Drag & Drop your file or <span class="filepond--label-action">Browse</span>',
                    validate: () => {
                        const field = this.broker.input.fileAuthorization;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Authorization Document is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                // fileContract: new fields.file({
                //     name: 'fileContract',
                //     allowMultiple: false,
                //     accept: 'application/pdf',
                //     maxFileSize: '10MB',
                //     labelIdle: 'Drag & Drop your PDF or <span class="filepond--label-action">Browse</span>',
                //     validate: () => {
                //         const field = this.broker.input.fileContract;
                //         let message = null;
                //         let valid = true;
                //         if (!field.value) {
                //             message = _t('Contract is required');
                //             valid = false;
                //         }
                //         this._onFieldValid(field, valid, message);
                //         return valid;
                //     }
                // }),
            },
            otp: {
                input1: new fields.element(),
                input2: new fields.element(),
                input3: new fields.element(),
                input4: new fields.element(),
            }
        };
    },

    start: function () {
        const self = this;
        return this._super.apply(this, arguments).then(() => {
            self._initializeOtpInputs();
            self._initializeUserTypeToggle();
        });
    },

    _initializeUserTypeToggle: function() {
        const self = this;
        const $form = this.$('#brokerInfoForm');
        const $radioInd = $form.find('input[name="userType"][value="individual"]');
        const $radioCor = $form.find('input[name="userType"][value="corporate"]');
        const $individualFields = $form.find('.individual-fields');
        const $corporateFields = $form.find('.corporate-fields');
        const $slider = $form.find('.radioTab__slider');
        
        function setMode(mode) {
            const isInd = mode === 'individual';
            
            // Toggle visibility
            $individualFields.toggleClass('d-none', !isInd).toggle(isInd);
            $corporateFields.toggleClass('d-none', isInd).toggle(!isInd);
            
            // Update radio buttons
            $radioInd.prop('checked', isInd);
            $radioCor.prop('checked', !isInd);
            
            // Move slider
            if ($slider.length) {
                $slider.css('transform', isInd ? 'translateX(0%)' : 'translateX(100%)');
            }
            
            // Set required attributes
            $individualFields.find('input').prop('required', isInd);
            $corporateFields.find('input').prop('required', !isInd);
            
            // Clear errors
            if (isInd) {
                $corporateFields.find('.form__group').removeClass('-error');
                $corporateFields.find('.form__icon').removeClass('fa-times-circle fa-check-circle');
            } else {
                $individualFields.find('.form__group').removeClass('-error');
                $individualFields.find('.form__icon').removeClass('fa-times-circle fa-check-circle');
            }
        }
        
        // Remove old listeners
        $radioInd.off('change.userTypeToggle');
        $radioCor.off('change.userTypeToggle');
        
        // Add new listeners
        if ($radioInd.length) {
            $radioInd.on('change.userTypeToggle', () => {
                if ($radioInd.is(':checked')) setMode('individual');
            });
        }
        if ($radioCor.length) {
            $radioCor.on('change.userTypeToggle', () => {
                if ($radioCor.is(':checked')) setMode('corporate');
            });
        }
        
        const selected = $form.find('input[name="userType"]:checked').val() || 'corporate';
        setMode(selected);
    },

    _isVatValid: function(value) {
        if (value.length === 10) {
            let v = [];
            let lastDigit = Number(value.charAt(9));
            for (let i = 0; i < 9; i++) {
                let tmp = (Number(value.charAt(i)) + (9 - i)) % 10;
                v[i] = (tmp * 2 ** (9 - i)) % 9;
                if (tmp !== 0 && v[i] === 0) v[i] = 9;
            }
            let sum = v.reduce((a, b) => a + b, 0) % 10;
            return (10 - (sum % 10)) % 10 === lastDigit;
        }
        return false;
    },

    _isTcknValid: function(value) {
        if (!/^\d{11}$/.test(value)) {
            return false;
        }
        
        if (value[0] === '0') {
            return false;
        }
        
        const digits = value.split('').map(Number);
        
        let sum1 = 0, sum2 = 0;
        for (let i = 0; i < 9; i++) {
            if (i % 2 === 0) {
                sum1 += digits[i];
            } else {
                sum2 += digits[i];
            }
        }

        const check1 = ((sum1 * 7) - sum2) % 10;
        if (check1 !== digits[9]) {
            return false;
        }

        const totalSum = digits.slice(0, 10).reduce((a, b) => a + b, 0);
        const check2 = totalSum % 10;
        if (check2 !== digits[10]) {
            return false;
        }

        return true;
    },

    _isIbanValid: function(iban) {
        iban = iban.replace(/\s+/g, '').toUpperCase();
        if (!/^[A-Z0-9]+$/.test(iban)) {
            return false;
        }

        const rearranged = iban.slice(4) + iban.slice(0, 4);
        let expanded = '';
        for (let ch of rearranged) {
            const code = ch.charCodeAt(0);
            if (code >= 65 && code <= 90) {
                expanded += (code - 55).toString();
            } else {
                expanded += ch;
            }
        }

        let remainder = expanded;
        let block;
        let total = '';

        while (remainder.length > 0) {
            block = total + remainder.substring(0, 9);
            remainder = remainder.substring(9);
            total = (parseInt(block, 10) % 97).toString();
        }
        return parseInt(total, 10) === 1;
    },

    _initializeOtpInputs: function() {
        const self = this;
        const otpInputs = [
            this.broker.otp.input1,
            this.broker.otp.input2,
            this.broker.otp.input3,
            this.broker.otp.input4,
        ];

        otpInputs.forEach((input, index) => {
            input.$.on('input', function(e) {
                const value = this.value.replace(/\D/g, '');
                this.value = value.slice(0, 1);
                if (this.value && index < 3) {
                    otpInputs[index + 1].$.focus();
                }
                if (this.value && index === 3) {
                    const code = otpInputs.map(inp => inp.$.val()).join('');
                    if (code.length === 4) {
                        setTimeout(function() {
                            self.broker.button.otpSubmit.$.trigger('click');
                        }, 300);
                    }
                }
            });

            input.$.on('keydown', function(e) {
                if (e.key === 'Backspace' && !this.value && index > 0) {
                    otpInputs[index - 1].$.focus();
                }
            });

            input.$.on('paste', function(e) {
                e.preventDefault();
                const pastedData = e.originalEvent.clipboardData.getData('text');
                const digits = pastedData.replace(/\D/g, '').slice(0, 4);
                
                digits.split('').forEach((digit, i) => {
                    if (otpInputs[i]) {
                        otpInputs[i].$.val(digit);
                    }
                });
                
                if (digits.length > 0) {
                    const lastIndex = Math.min(digits.length - 1, 3);
                    otpInputs[lastIndex].$.focus();
                    
                    if (digits.length === 4) {
                        self.broker.button.otpSubmit.$.trigger('click');
                    }
                }
            });
        });
    },

    _onPhoneInput: function() {
        const self = this;
        const field = this.broker.input.phone;
        
        if (this.phoneVerified) {
            this.phoneVerified = false;
            this._hideFieldIcon(field);
        }
    },

    _showOtpModal: function(expiresIn) {
        const self = this;
        const $modal = $('#brokerOtpModal');
        const $timer = $('#brokerOtpTimer');
        const $submitBtn = $('#brokerOtpSubmit');
        const $resendBtn = $('#brokerOtpResend');
        
        let seconds = expiresIn || 120;

        $modal.css('display', 'flex');

        $timer.text(seconds);
        if (this.otpTimer) {
            clearInterval(this.otpTimer);
        }

        this.otpTimer = setInterval(() => {
            seconds -= 1;
            if (seconds < 0) seconds = 0;
            $timer.text(seconds);
            
            if (seconds === 0) {
                clearInterval(self.otpTimer);
                $submitBtn.prop('disabled', true).addClass('disabled');
                $resendBtn.show();
            }
        }, 1000);

        this.broker.otp.input1.$.focus();
        
        [this.broker.otp.input1, this.broker.otp.input2, this.broker.otp.input3, this.broker.otp.input4].forEach(input => {
            input.$.val('');
        });
    },

    _closeOtpModal: function() {
        const $modal = $('#brokerOtpModal');
        $modal.hide();
        
        if (this.otpTimer) {
            clearInterval(this.otpTimer);
            this.otpTimer = null;
        }
        
        $('#brokerOtpSubmit').prop('disabled', false).removeClass('disabled');
        $('#brokerOtpResend').hide();
    },

    _onClickOtpSubmit: function(ev) {
        ev.preventDefault();
        const self = this;

        const code = [
            this.broker.otp.input1.$.val(),
            this.broker.otp.input2.$.val(),
            this.broker.otp.input3.$.val(),
            this.broker.otp.input4.$.val(),
        ].join('');

        if (code.length !== 4) {
            this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Please enter 4-digit code'),
                });
            return;
        }

        rpc.query({
            route: '/broker/otp/verify',
            params: {
                otp_id: this.otpId,
                code: code,
            }
        }).then(function(result) {
            if (result && result.success) {
                self.phoneVerified = true;
                self._closeOtpModal();
                self._showFieldSuccessIcon(self.broker.input.phone);
                
                self.broker.input.phone.$.closest('.form__group').find('.phone-verification-notice, .form__error-label, .just-validate-error-label').remove();
                self.broker.input.phone.$.removeClass('is-invalid -error just-validate-error-field').addClass('is-valid');
                self.displayNotification({
                        type: 'success',
                        title: _t('Success'),
                        message: _t('Phone number verified successfully'),
                    });
                setTimeout(function() {
                    self.broker.button.next.$.trigger('click');
                }, 500);
            } else {
                self.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: result.message || _t('Invalid verification code'),
                    });
                [self.broker.otp.input1, self.broker.otp.input2, self.broker.otp.input3, self.broker.otp.input4].forEach(input => {
                    input.$.val('');
                });
                self.broker.otp.input1.$.focus();
            }
        }).catch(function(error) {
            console.error('Error verifying OTP:', error);
            self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occurred during verification'),
                });
        });
    },

    _onClickOtpCancel: function(ev) {
        ev.preventDefault();
        this._closeOtpModal();
    },

    _onClickOtpResend: function(ev) {
        ev.preventDefault();
        const self = this;
        
        rpc.query({
            route: '/my/otp/start',
            params: { partner_id: self.partner }
        }).then(function(result) {
            if (result && result.success) {
                self.otpId = result.otp_id;
                self.displayNotification({
                    type: 'success',
                    title: _t('Success'),
                    message: _t('Verification code sent again'),
                });
                $('#brokerOtpResend').hide();
                self._showOtpModal(result.expires_in || 120);
            } else {
                self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: result.message || _t('Failed to resend OTP'),
                });
            }
        }).catch(function(error) {
            console.error('Error resending OTP:', error);
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occurred while resending OTP'),
            });
        });
    },

    _showFieldSuccessIcon: function(field) {
        const $icon = field.$.closest('.form__group').find('.form__icon');
        $icon.removeClass('fa-exclamation-circle fa-spinner fa-spin').addClass('fa-check-circle');
    },

    _showFieldErrorIcon: function(field) {
        const $icon = field.$.closest('.form__group').find('.form__icon');
        $icon.removeClass('fa-check-circle fa-spinner fa-spin').addClass('fa-exclamation-circle');
    },

    _showFieldLoadingIcon: function(field) {
        const $icon = field.$.closest('.form__group').find('.form__icon');
        $icon.removeClass('fa-check-circle fa-exclamation-circle').addClass('fa-spinner fa-spin');
    },

    _hideFieldIcon: function(field) {
        const $icon = field.$.closest('.form__group').find('.form__icon');
        $icon.removeClass('fa-check-circle fa-exclamation-circle fa-spinner fa-spin');
    },

    _onClickNext: function(ev) {
        ev.preventDefault();
        const self = this;
        
        const userType = this.$('input[name="userType"]:checked').val();
        const isIndividual = userType === 'individual';
        
        let fields = [];
        
        if (isIndividual) {
            fields = [
                this.broker.input.vat,
                this.broker.input.name,
                this.broker.input.state,
                this.broker.input.city,
                this.broker.input.person,
                this.broker.input.phone,
                this.broker.input.email,
                this.broker.input.iban,
                this.broker.input.iban_name,
            ];
        } else {
            fields = [
                this.broker.input.tax_number,
                this.broker.input.company_title,
                this.broker.input.sign_name,
                this.broker.input.state,
                this.broker.input.city,
                this.broker.input.person,
                this.broker.input.phone,
                this.broker.input.email,
                this.broker.input.iban,
                this.broker.input.iban_name,
            ];
        }

        let isValid = true;
        fields.forEach(field => {
            if (field.validate && !field.validate()) {
                isValid = false;
            }
        });

        if (!isValid) {
            return;
        }
        
        const formData = {
            step: 1,
            user_type: userType,
            state_id: this.broker.input.state.value,
            city: this.broker.input.city.value,
            person: this.broker.input.person.value,
            phone: this.broker.input.phone.value,
            email: this.broker.input.email.value,
            iban: this.broker.input.iban.$.val(),
            iban_name: this.broker.input.iban_name.value,
        };
        
        if (isIndividual) {
            formData.vat = this.broker.input.vat.value;
            formData.name = this.broker.input.name.value;
            formData.sign_name = this.broker.input.sign_name.value;
        } else {
            formData.tax_number = this.broker.input.tax_number.value;
            formData.company_title = this.broker.input.company_title.value;
            formData.sign_name = this.broker.input.sign_name.value;
        }

        this.broker.button.next.$.prop('disabled', true);

        rpc.query({
            route: '/broker/register/save',
            params: formData,
        }).then(function(result) {
            if (result.success) {
                self.partner = result.partner_id || self.tempPartnerId || 0;
                
                if (!self.phoneVerified) {
                    self._showFieldLoadingIcon(self.broker.input.phone);
                    
                    rpc.query({
                        route: '/broker/otp/start',
                        params: { partner_id: self.partner }
                    }).then(function(result) {
                        if (result && result.success) {
                            self.otpId = result.otp_id;
                            self._showOtpModal(result.expires_in || 120);
                            self._hideFieldIcon(self.broker.input.phone);
                        } else if (result && result.is_otp_verified) {
                            self.phoneVerified = true;
                            self._showFieldSuccessIcon(self.broker.input.phone);
                            // Step 2'ye geç
                            self._markStepCompleted(1);
                            $('.broker-step-1').removeClass('d-flex').addClass('d-none');
                            $('.broker-step-2').removeClass('d-none').addClass('d-flex');
                            $('.steps__item').eq(0).removeClass('-active').addClass('-completed');
                            $('.steps__item').eq(1).addClass('-active');
                        } else {
                            self.displayNotification({
                                type: 'danger',
                                title: _t('Error'),
                                message: result.message || _t('Failed to send OTP'),
                            });
                            self._hideFieldIcon(self.broker.input.phone);
                        }
                    }).catch(function(error) {
                        console.error('Error starting OTP:', error);
                        self.displayNotification({
                            type: 'danger',
                            title: _t('Error'),
                            message: _t('An error occurred while sending OTP'),
                        });
                        self._hideFieldIcon(self.broker.input.phone);
                    });
                    return;
                }
                
                self._markStepCompleted(1);
                $('.broker-step-1').removeClass('d-flex').addClass('d-none');
                $('.broker-step-2').removeClass('d-none').addClass('d-flex');
                
                $('.steps__item').eq(0).removeClass('-active').addClass('-completed');
                $('.steps__item').eq(1).addClass('-active');
            } else {
                self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occurred' + (result.message ? (': ' + result.message) : '')),
                });
            }
        }).catch(function(error) {
            console.error('Error:', error);
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occurred while processing your request'),
            });
        }).finally(function() {
            self.broker.button.next.$.prop('disabled', false);
        });
    },

    _onClickBack: function(ev) {
        ev.preventDefault();
        $('.broker-step-2').removeClass('d-flex').addClass('d-none');
        $('.broker-step-1').removeClass('d-none').addClass('d-flex');
        
        $('.steps__item').eq(1).removeClass('-active');
        $('.steps__item').eq(0).addClass('-active');
    },

    _onClickSubmit: function(ev) {
        ev.preventDefault();
        const self = this;

        const fileFields = [
            this.broker.input.fileTaxPlate,
            this.broker.input.fileSignatureCircular,
            this.broker.input.fileIdentity,
            this.broker.input.fileAuthorization,
            // this.broker.input.fileContract,
        ];

        let isValid = true;
        fileFields.forEach(field => {
            if (field.validate && !field.validate()) {
                isValid = false;
            }
        });

        if (!isValid) {
            return;
        }

        if (this.agreement && this.agreement.exist && !this.agreement.confirmed) {
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('Please accept all required agreements'),
            });
            return;
        }

        if (!this.partner) {
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('Session expired. Please start over.'),
            });
            return;
        }

        const formData = {
            step: 2,
            partner_id: this.partner,
            tax_plate: this.broker.input.fileTaxPlate.value,
            tax_plate_filename: this.broker.input.fileTaxPlate.filename || 'tax_plate.pdf',
            signature_circular: this.broker.input.fileSignatureCircular.value,
            signature_circular_filename: this.broker.input.fileSignatureCircular.filename || 'signature_circular.pdf',
            identity_doc: this.broker.input.fileIdentity.value,
            identity_doc_filename: this.broker.input.fileIdentity.filename || 'identity.pdf',
            authorization_doc: this.broker.input.fileAuthorization.value,
            authorization_doc_filename: this.broker.input.fileAuthorization.filename || 'authorization.pdf',
            // contract: this.broker.input.fileContract.value,
            // contract_filename: this.broker.input.fileContract.filename || 'contract.pdf',
        };

        if (this.agreement && this.agreement.exist) {
            formData.agreements = Object.entries(this.agreement.all)
                .filter(([k, v]) => v.checked)
                .map(x => Number(x[0]));
        }

        this.broker.button.submit.$.prop('disabled', true);

        rpc.query({
            route: '/broker/register/save',
            params: formData,
        }).then(function(result) {
            if (result.success) {
                self._markStepCompleted(2);
                $('.broker-step-2').removeClass('d-flex').addClass('d-none');
                $('.broker-step-3').removeClass('d-none').addClass('d-flex');
                $('.steps__item').addClass('-completed completed');
                self.displayNotification({
                    type: 'success',
                    title: _t('Success'),
                    message: result.message || _t('Registration submitted successfully'),
                });
            } else {
                self.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: result.message || _t('An error occurred'),
                });
                self.broker.button.submit.$.prop('disabled', false);
            }
        }).catch(function(error) {
            console.error('Error:', error);
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occurred while submitting your registration'),
            });
            self.broker.button.submit.$.prop('disabled', false);
        });
    },

    _onFieldValid: function(field, valid, message = '') {
        if (!field || !field.$) return;
        field.$.closest('.form__group').find('.form__error-label, .just-validate-error-label').remove();
        
        if (valid) {
            field.$.removeClass('is-invalid -error just-validate-error-field').addClass('is-valid');
            const $icon = field.$.siblings('.form__icon');
            $icon.removeClass('fa-times-circle').addClass('fa-check-circle');
        } else {
            field.$.addClass('is-invalid -error just-validate-error-field').removeClass('is-valid');
            const $icon = field.$.siblings('.form__icon');
            $icon.removeClass('fa-check-circle').addClass('fa-times-circle');
            if (message) {
                field.$.closest('.form__group').append($(`<div class="form__error-label just-validate-error-label">${message}</div>`));
            }
        }
    },

    _markStepCompleted: function (stepNumber) {
        if (stepNumber >= 1 && stepNumber <= 2) {
            const $stepItem = $(`.steps__item:nth-child(${stepNumber})`);
            $stepItem.addClass('-completed');
        }
    },
});