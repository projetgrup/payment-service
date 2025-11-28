/** @odoo-module alias=paylox.system.escrow **/
'use strict';

import rpc from 'web.rpc';
import dialog from 'web.Dialog';
import { _t, qweb } from 'web.core';
import publicWidget from 'web.public.widget';
import framework from 'paylox.framework';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';
import { format } from 'paylox.tools';

const REGEXP_EMAIL = /^((?!\.)[\w\-_.]*[^.])(@\w+)(\.\w+(\.\w+)?[^.\W])$/;

publicWidget.registry.payloxSystemEscrow = publicWidget.Widget.extend({
    selector: '.payment-escrow #wrapwrap',
    jsLibs: [
        '/payment_jetcheckout/static/src/lib/imask/imask.js',
        '/payment_jetcheckout/static/src/lib/filepond/filepond.js',
    ],
    xmlDependencies: ['/payment_escrow/static/src/xml/templates.xml'],

    init: function (parent, options) {
        this._super(parent, options);
        this.values = {
            ads: {},
        };
        this.state = {
            id: 0,
            step: 0,
            owner: 0,
            customer: 0,
            status: '',
            different: false,
            filterState: 'all',
            pagination: {
                currentPage: 1,
                pageSize: 10,
                totalItems: 0,
                totalPages: 1,
                filteredAds: []
            }
        };
        this.filterState = {
            search: '',
            category: 'all',
            state: 'all',
            priceMin: null,
            priceMax: null
        };
        this.transaction = []
        this.currency = {
            id: 0,
            decimal: 2,
            name: '',
            separator: '.',
            thousand: ',', 
            position: 'after',
            symbol: '', 
        };
        this.wizard = {
            lookup: false,
            button: {
                next: new fields.element({
                    events: [['click', this._nextStep]]
                }),
                previous: new fields.element({
                    events: [['click', this._onClickWizardPrevious]]
                }),
                close: new fields.element({
                    events: [['click', this._onClickWizardClose]]
                }),
                submit: new fields.element({
                    events: [['click', this._onClickWizardSubmit]]
                }),
            },
            file: new fields.element({
                events: [['change', this._onFileChange]]
            }),
            loading: new fields.element()
        };
        this.amount = new fields.float({
            events: [
                ['update', function() { this.amount._.updateValue(); }],
            ],
            mask: payloxPage.prototype._maskAmount.bind(this),
            default: 0,
            validate: () => {
                const field = this.amount;
                let message = null;
                let valid = true;
                let value = field.value;
                if (field.value <= 0) {
                    message = _t('Price must be positive');
                    valid = false;
                    value = 0;
                } else if (!field.value && !field._.masked.isComplete) {
                    message = _t('Price is required');
                    valid = false;
                    value = 0;
                }
                this._onFieldValid(field, valid, message);
                this._onInputAmount();
                return valid;
            }
        });
        this.installment = {
            row: new fields.string({
                events: [['click', this._onClickInstallmentRow]],
            }),
        };
        this.partner = new fields.integer({
            default: 0,
        });
        this.$otpModal = null;
        this.otpTimer = null;
        this.shouldAdvanceStep = false;
        this.currentOtpPartnerId = 0;
        this.seller = {
            wizard: new fields.element(),
            ads: new fields.element(),
            button: {
                close: new fields.element({ events: [['click', this._onClickWizardClose]] }),
            },
            input: {
                name: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.name;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field.value) {
                                message = _t('Name is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('name is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                city_individual: new fields.string({
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.city_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field.value) {
                                message = _t('City is required');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                tc: new fields.float({
                    events: [['input', () => {
                        const sellerType = $('input[name="userType"]:checked').val();
                        this._lookupPartnerByIdentity('seller', sellerType, this.seller.input.tc.value, 11);
                    }]],
                    mask: '00000000000',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.tc;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field._.masked.isComplete) {
                                message = _t('Tax ID is required');
                                valid = false;
                            } else if (!this._isTcknValid(field.value)) {
                                message = _t('Tax ID is not valid');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                phone_individual: new fields.string({
                    events: [['input', () => this._isOtpValidate(this.seller.input.phone_individual)]],
                    mask: '000 000 0000',
                    validate: async () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.phone_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                }),
                email_individual: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.email_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                if (!field._.masked.isComplete || !REGEXP_EMAIL.test(field.value)) {
                                    message = _t('Email format is not correct');
                                    valid = false;
                                }
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                iban_individual: new fields.string({
                    events: [['input', () => this._isIbanVerified(this.seller.input.iban_individual, this.seller.input.tc)]],
                    mask: 'TR00 0000 0000 0000 0000 0000 00',
                    validate: async () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.iban_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field._.masked.isComplete) {
                                message = _t('IBAN is required');
                                valid = false;
                            } else if (!this._isIbanValid(field._.masked.value)) {
                                message = _t('IBAN is not valid');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                }),
                iban_name_individual: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.iban_name_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field.value) {
                                message = _t('IBAN name is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('IBAN name is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                corporate_title: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.corporate_title;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('Corporate title is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('Corporate title is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                city_corporate: new fields.string({
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.city_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('City is required');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                tax_number: new fields.string({
                    events: [['input', () => {
                        const sellerType = $('input[name="userType"]:checked').val();
                        this._lookupPartnerByIdentity('seller', sellerType, this.seller.input.tax_number.value, 10);
                    }]],
                    mask: '0000000000',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.tax_number;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field._.masked.isComplete) {
                                message = _t('Tax ID is required');
                                valid = false;
                            } else if (!this._isVatValid(field.value)) {
                                message = _t('Tax ID is not valid');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                /*tax_office: new fields.string({
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.tax_office;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate'&& !field.value) {
                            message = _t('Tax Office title is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),*/
                corporate_person: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.corporate_person;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('Corporate person is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('Corporate person is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                phone_corporate: new fields.string({
                    events: [['input', () => this._isOtpValidate(this.seller.input.phone_corporate)]],
                    mask: '000 000 0000',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.phone_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                }),
                email_corporate: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.email_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                if (!field._.masked.isComplete || !REGEXP_EMAIL.test(field.value)) {
                                    message = _t('Email format is not correct');
                                    valid = false;
                                }
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                iban_corporate: new fields.string({
                    events: [['input', () => this._isIbanVerified(this.seller.input.iban_corporate, this.seller.input.tax_number)]],
                    mask: 'TR00 0000 0000 0000 0000 0000 00',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.iban_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field._.masked.isComplete) {
                                message = _t('IBAN is required');
                                valid = false;
                            } else if (!this._isIbanValid(field._.masked.value)) {
                                message = _t('IBAN is not valid');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                    check: new fields.element(),
                    error: new fields.element()
                }),
                iban_name_corporate: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.iban_name_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('IBAN name is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('IBAN name is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
            }
        };

        this.customer = {
            input: {
                tc: new fields.string({
                    events: [['input', () => {
                        const type = $('input[name="customerUserType"]:checked').val();
                        this._lookupPartnerByIdentity('customer', type, this.customer.input.tc.value, 11);
                    }]],
                    mask: '00000000000',
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.tc;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field._.masked.isComplete) {
                                message = _t('Tax ID is required');
                                valid = false;
                            } else if (!this._isTcknValid(field.value)) {
                                message = _t('Tax ID is not valid');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                name: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.name;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field.value) {
                                message = _t('Name is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('name is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                phone_individual: new fields.string({
                    events: [['input', () => this._isOtpValidate(this.customer.input.phone_individual)]],
                    mask: '000 000 0000',
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.phone_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                }),
                email_individual: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.email_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual') {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                if (!field._.masked.isComplete || !REGEXP_EMAIL.test(field.value)) {
                                    message = _t('Email format is not correct');
                                    valid = false;
                                }
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                address_individual: new fields.string({
                   validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.address_individual;
                        let message = null;
                        let valid = true;
                        if (mod === 'individual' && !field.value) {
                            message = _t('Address is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                corporate_title: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.corporate_title;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('Corporate title is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('Corporate title is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                tax_number: new fields.string({
                    events: [['input', () => {
                        const type = $('input[name="customerUserType"]:checked').val();
                        this._lookupPartnerByIdentity('customer', type, this.customer.input.tax_number.value, 10);
                    }]],
                    mask: '0000000000',
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.tax_number;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field._.masked.isComplete) {
                                message = _t('Tax ID is required');
                                valid = false;
                            } else if (!this._isVatValid(field.value)) {
                                message = _t('Tax ID is not valid');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                tax_office: new fields.string({
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.tax_office;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate'&& !field.value) {
                            message = _t('Tax office is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                corporate_person: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.corporate_person;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('Corporate person is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('Corporate person is not correct');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                phone_corporate: new fields.string({
                    events: [['input', () => this._isOtpValidate(this.customer.input.phone_corporate)]],
                    mask: '000 000 0000',
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.phone_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                }),
                email_corporate: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.email_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate') {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                if (!field._.masked.isComplete || !REGEXP_EMAIL.test(field.value)) {
                                    message = _t('Email format is not correct');
                                    valid = false;
                                }
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                address_corporate: new fields.string({
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.address_corporate;
                        let message = null;
                        let valid = true;
                        if (mod === 'corporate'&& !field.value) {
                            message = _t('Address is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                fileConveyance: new fields.file({
                    name: 'fileConveyance',
                    allowMultiple: false,
                    accept: 'image/*, application/pdf',
                    maxFileSize: '10MB',
                    className: 'escrow-wizard-file',
                    labelIdle: `<svg class="w-100" width="42" height="42" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M31.4998 33.2514C30.5318 33.2514 29.7484 32.468 29.7484 31.5C29.7484 30.532 30.5318 29.7486 31.4998 29.7486C35.3594 29.7486 38.5012 26.6068 38.5012 22.7473C38.5012 19.0723 35.626 16.0084 31.9592 15.7705L30.9256 15.709L30.4867 14.7779C28.7559 11.1152 25.0316 8.74863 20.9998 8.74863C16.968 8.74863 13.2438 11.1152 11.5129 14.7779L11.074 15.709L10.0445 15.7746C6.37363 16.0125 3.50254 19.0764 3.50254 22.7514C3.50254 26.6109 6.64434 29.7527 10.5039 29.7527C11.4719 29.7527 12.2553 30.5361 12.2553 31.5041C12.2553 32.4721 11.4719 33.2555 10.5039 33.2555C4.7125 33.2555 0.00390625 28.5469 0.00390625 22.7555C0.00390625 17.5834 3.79785 13.2193 8.80996 12.4031C11.2709 8.02676 15.9508 5.25 20.9998 5.25C26.0488 5.25 30.7287 8.02676 33.1938 12.3949C38.2059 13.2111 41.9998 17.5793 41.9998 22.7514C41.9998 28.5387 37.2912 33.2514 31.4998 33.2514Z" fill="black"/>
                            <path d="M26.2502 32.3737C25.8032 32.3737 25.3561 32.2014 25.0116 31.861L21.0002 27.8497L16.9889 31.861C16.3081 32.5459 15.1965 32.5459 14.5157 31.861C13.8307 31.176 13.8307 30.0686 14.5157 29.3877L19.7657 24.1377C20.4465 23.4528 21.5581 23.4528 22.2389 24.1377L27.4889 29.3877C28.1739 30.0727 28.1739 31.1801 27.4889 31.861C27.1444 32.2055 26.6973 32.3737 26.2502 32.3737Z" fill="#2414D8"/>
                            <path d="M21.0004 39.375C20.0324 39.375 19.249 38.5916 19.249 37.6236V25.3764C19.249 24.4084 20.0324 23.625 21.0004 23.625C21.9684 23.625 22.7518 24.4084 22.7518 25.3764V37.6277C22.7518 38.5916 21.9684 39.375 21.0004 39.375Z" fill="#2414D8"/>
                        </svg>
                        <span class="text-600">Select Image or Take New</span>
                        <div class="text-600">No Image Selected</div>`,
                    validate: () => {
                        return true;
                    },
                }),
            }
        }

        this.insurance = {
            state: {
                brandRequestId: 0,
                modelRequestId: 0,
            },
            button: {
                submit: new fields.element({
                    events: [['click', this._onInsuranceSubmit]]
                })
            },
            alert: {
                success: new fields.element(),
                error: new fields.element()
            },
            success: {
                message: new fields.element()
            },
            error: {
                message: new fields.element()
            },
            input: {
                birth_date: new fields.string({
                    mask: '00/00/0000',
                    validate: () => {
                        const field = this.insurance.input.birth_date;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Birth date is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                vat: new fields.string({
                    mask: /^\d{0,11}$/,
                    validate: () => {
                        const field = this.insurance.input.vat;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('TC Identity Number is required');
                            valid = false;
                        } else if (field.value.length !== 11) {
                            message = _t('TC Identity Number must be 11 digits');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                gsmNo: new fields.string({
                    mask: /^[0-9]{0,10}$/,
                    validate: () => {
                        const field = this.insurance.input.gsmNo;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Mobile number is required');
                            valid = false;
                        } else if (field.value.length !== 10) {
                            message = _t('Mobile number must be 10 digits');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                email: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const field = this.insurance.input.email;
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
                plate: new fields.string({
                    mask: /^[A-Za-z0-9]*$/,
                    events: [['input', function() {
                        const field = this.insurance.input.plate;
                        field.$.val(field.$.val().toUpperCase());
                    }]],
                    validate: () => {
                        const field = this.insurance.input.plate;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('License plate is required');
                            valid = false;
                        } else {
                            const cleanPlate = field.value.replace(/\s/g, '');
                            const platePattern = /^[0-9]{2}[A-Z]{1,3}[0-9]{1,4}$/;
                            if (!platePattern.test(cleanPlate)) {
                                message = _t('Please enter a valid license plate (e.g., 34TM3405)');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                license_no: new fields.string({
                    mask: /^[A-Z0-9]{0,8}$/,
                    validate: () => {
                        const field = this.insurance.input.license_no;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('License serial number is required');
                            valid = false;
                        } else if (field.value.length !== 8) {
                            message = _t('License serial number must be 8 characters');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                chassis_no: new fields.string({
                    mask: /^[A-Z0-9]{0,17}$/,
                    validate: () => {
                        const field = this.insurance.input.chassis_no;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Chassis number is required');
                            valid = false;
                        } else if (field.value.length !== 17) {
                            message = _t('Chassis number must be 17 characters');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                // engine_no: new fields.string({
                //     validate: () => {
                //         const field = this.insurance.input.engine_no;
                //         let message = null;
                //         let valid = true;
                //         if (!field.value) {
                //             message = _t('Engine number is required');
                //             valid = false;
                //         }
                //         this._onFieldValid(field, valid, message);
                //         return valid;
                //     }
                // }),
                // registration_date: new fields.string({
                //     validate: () => {
                //         const field = this.insurance.input.registration_date;
                //         let message = null;
                //         let valid = true;
                //         if (!field.value) {
                //             message = _t('Registration date is required');
                //             valid = false;
                //         }
                //         this._onFieldValid(field, valid, message);
                //         return valid;
                //     }
                // }),
                brand: new fields.selection({
                    events: [['change', this._onInsuranceBrandChange]],
                    validate: () => {
                        const field = this.insurance.input.brand;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Vehicle brand is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                model: new fields.selection({
                    validate: () => {
                        const field = this.insurance.input.model;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Vehicle model is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                year: new fields.string({
                    events: [
                        ['blur', this._onInsuranceYearChange],
                        ['change', this._onInsuranceYearChange],
                    ],
                    mask: /^\d{0,4}$/,
                    validate: () => {
                        const field = this.insurance.input.year;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Model year is required');
                            valid = false;
                        } else if (field.value.length !== 4) {
                            message = _t('Model year must be 4 digits');
                            valid = false;
                        } else {
                            const year = parseInt(field.value);
                            const currentYear = new Date().getFullYear();
                            if (year < 1900 || year > currentYear + 1) {
                                message = _t('Invalid model year');
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
            }
        };

        this.ad = {
            state: {
                filter: new fields.element(),
                all: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                new: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                waiting: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                draft: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                waiting_payment: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                waiting_official_doc: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                waiting_transfer: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                transferred: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                sold: new fields.element({ events: [['click', this._onStateFilterClick]] }),
                cancelled: new fields.element({ events: [['click', this._onStateFilterClick]] })
            },
            sort: new fields.selection({ 
                default: 'date_desc',
                events: [['change', this._onSortChange]] 
            }),
            pagination: {
                container: new fields.element(),
                prev: new fields.element({ events: [['click', this._onPaginationPrev]] }),
                next: new fields.element({ events: [['click', this._onPaginationNext]] }),
                current: new fields.element(),
                showing: new fields.element(),
                total: new fields.element(),
                size: new fields.selection({ 
                    default: '10',
                    events: [['change', this._onPaginationSizeChange]] 
                })
            },
            sideback: new fields.element(),
            sidebar: new fields.element(),
            button: {
                sidebar: {
                    toggle: new fields.element({
                        events: [['click', this._onClickButtonSidebarToggle]],
                    }),
                },
                list: new fields.element({
                    events: [['click', this._onClickButtonList]],
                }),
                grid: new fields.element({
                    events: [['click', this._onClickButtonGrid]],
                }),
                form: new fields.element({
                    events: [['click', this._onClickButtonForm]],
                }),
                create: new fields.element({
                    events: [['click', this._onClickButtonCreate]],
                }),
            },

            input: {
                price: new fields.float({
                    events: [
                        ['update', function() { this.ad.input.price._.updateValue(); }],
                    ],
                    mask: payloxPage.prototype._maskAmount.bind(this),
                    validate: () => {
                        const field = this.ad.input.price;
                        let message = null;
                        let valid = true;
                        if (field.value <= 0) {
                            message = _t('Price must be positive');
                            valid = false;
                        } else if (!field.value && !field._.masked.isComplete) {
                            message = _t('Price is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                category: new fields.selection({
                    events: [['change', this._onCategoryChange]],
                    validate: () => {
                        const field = this.ad.input.category;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Category is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
            },
            view: {
                list: new fields.element(),
                grid: new fields.element(),
                form: new fields.element(),
            },
            item: new fields.element({
                events: [['click', this._onClickAd]],
            }),
        };

        this.edit = {
            vehicle: {
                holder: new fields.element({
                    events: [['click', this._onToggleVehicleHolder]]
                })
            },
            seller: {
                holder: new fields.element({
                    events: [['click', this._onToggleSellerHolder]]
                })
            }
        };

        this.card = {
            holder: new fields.element({
                validate: () => {
                    const field = this.card.holder;
                    const different = this.payment.different.info.name;
                    let message = null;
                    let valid = true;
                    if (!field.value) {
                        message = _t('Holder is required');
                        valid = false;
                    } else if (this.state.different && field.value !== different.value) {
                        message = _t('Holder name must match the name entered in payment information');
                        valid = false;
                    }
                    this._onFieldValid(field, valid, message);
                    return valid;
                }
            }),
            number: new fields.string({
                events: [['input', this._onClickButtonPayment]],
                mask: '0000 0000 0000 0000',
            })
        }

        this.payment = {
            button: new fields.element({ events: [['click', this._onClickButtonPayment]] }),
            different: {
                holder: new fields.boolean({
                    events: [['change', this._onToggleDifferentHolder]]
                }),
                info: {
                    form: new fields.element(),
                    container: new fields.element(),
                    edit: new fields.element({     
                        events: [['click', this._onEditPaymentInfo]]
                    }),
                    cancel: new fields.element({ 
                        events: [['click', this._onCancelEditPaymentInfo]]
                    }),
                    save: new fields.element({
                        events: [['click', this._onSavePaymentInfo]]
                    }),
                    tc: new fields.string({
                        mask: '00000000000',
                        validate: () => {
                            const field = this.payment.different.info.tc;
                            let message = null;
                            let valid = true;
                            if (!field._.masked.isComplete) {
                                message = _t('Tax ID is required');
                                valid = false;
                            } else if (!this._isTcknValid(field.value)) {
                                message = _t('Tax ID is not valid');
                                valid = false;
                            }
                            this._onFieldValid(field, valid, message);
                            return valid;
                        }
                    }),
                    name: new fields.string({
                        events: [['input', () => {
                            const $cardHolder = $('#card_holder_name');
                            $cardHolder.val(this.payment.different.info.name.value);
                            $cardHolder.trigger('input');
                        }]],
                        mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                        prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                        validate: () => {
                            const field = this.payment.different.info.name;
                            let message = null;
                            let valid = true;
                            if (!field.value) {
                                message = _t('Name is required');
                                valid = false;
                            } else if (!field._.masked.isComplete) {
                                message = _t('name is not correct');
                                valid = false;
                            }
                            this._onFieldValid(field, valid, message);
                            return valid;
                        }
                    }),
                    phone: new fields.string({
                        events: [['input', () => this._isOtpValidate(this.payment.different.info.phone)]],
                        mask: '000 000 0000',
                        validate: () => {
                            const field = this.payment.different.info.phone;
                            let message = null;
                            let valid = true;
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            } 
                            this._onFieldValid(field, valid, message);
                            return valid;
                        },
                        check: new fields.element(),
                        error: new fields.element()
                    }),
                    email: new fields.string({
                        mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                        validate: () => {
                            const field = this.payment.different.info.email;
                            let message = null;
                            let valid = true;
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                if (!field._.masked.isComplete || !REGEXP_EMAIL.test(field.value)) {
                                    message = _t('Email format is not correct');
                                    valid = false;
                                }
                            }
                            this._onFieldValid(field, valid, message);
                            return valid;
                        }
                    }),
                    fileOfficialSale: new fields.file({
                        name: 'fileOfficialSale',
                        allowMultiple: false,
                        accept: 'image/*',
                        maxFileSize: '15MB',
                        className: 'escrow-wizard-file',
                        labelIdle: `<svg class="w-100" width="42" height="42" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M31.4998 33.2514C30.5318 33.2514 29.7484 32.468 29.7484 31.5C29.7484 30.532 30.5318 29.7486 31.4998 29.7486C35.3594 29.7486 38.5012 26.6068 38.5012 22.7473C38.5012 19.0723 35.626 16.0084 31.9592 15.7705L30.9256 15.709L30.4867 14.7779C28.7559 11.1152 25.0316 8.74863 20.9998 8.74863C16.968 8.74863 13.2438 11.1152 11.5129 14.7779L11.074 15.709L10.0445 15.7746C6.37363 16.0125 3.50254 19.0764 3.50254 22.7514C3.50254 26.6109 6.64434 29.7527 10.5039 29.7527C11.4719 29.7527 12.2553 30.5361 12.2553 31.5041C12.2553 32.4721 11.4719 33.2555 10.5039 33.2555C4.7125 33.2555 0.00390625 28.5469 0.00390625 22.7555C0.00390625 17.5834 3.79785 13.2193 8.80996 12.4031C11.2709 8.02676 15.9508 5.25 20.9998 5.25C26.0488 5.25 30.7287 8.02676 33.1938 12.3949C38.2059 13.2111 41.9998 17.5793 41.9998 22.7514C41.9998 28.5387 37.2912 33.2514 31.4998 33.2514Z" fill="black"/>
                                <path d="M26.2502 32.3737C25.8032 32.3737 25.3561 32.2014 25.0116 31.861L21.0002 27.8497L16.9889 31.861C16.3081 32.5459 15.1965 32.5459 14.5157 31.861C13.8307 31.176 13.8307 30.0686 14.5157 29.3877L19.7657 24.1377C20.4465 23.4528 21.5581 23.4528 22.2389 24.1377L27.4889 29.3877C28.1739 30.0727 28.1739 31.1801 27.4889 31.861C27.1444 32.2055 26.6973 32.3737 26.2502 32.3737Z" fill="#2414D8"/>
                                <path d="M21.0004 39.375C20.0324 39.375 19.249 38.5916 19.249 37.6236V25.3764C19.249 24.4084 20.0324 23.625 21.0004 23.625C21.9684 23.625 22.7518 24.4084 22.7518 25.3764V37.6277C22.7518 38.5916 21.9684 39.375 21.0004 39.375Z" fill="#2414D8"/>
                            </svg>
                            <span class="text-600">Select Image or Take New</span>
                            <div class="text-600">No Image Selected</div>`,
                        validate: () => {
                            const field = this.ad.input.fileOfficialSale;
                            let message = null;
                            let valid = true;
                            if (!field.value) {
                                message = _t('Official sale image is required');
                                valid = false;
                            }
                            this._onFieldValid(field, valid, message);
                            return valid;
                        },
                    }),
                }
            },
            amount: {
                previous: new fields.element(),
                remaining: new fields.element(),
                total: new fields.element(),
                paid: new fields.element(),
            },
            transaction: {
                reference: new fields.element(),
                date: new fields.element(),
                status: new fields.element()
            },
            button: {
                return: new fields.element({
                    events: [['click', this._onClickReturnToPayment]]
                })
            }
        };

        this.assignment = {
            form: {
                section: new fields.element(),
                download: new fields.element({
                    events: [['click', this._onDownloadAssignmentForm]]
                }),
                upload: new fields.element({
                    events: [['change', this._onUploadAssignmentForm]]
                }),
                info: new fields.element(),
                'upload.status': new fields.element()
            }
        };
    },

    _startState: function () {
        let hash = new URLSearchParams(window.location.search).get('');
        if (hash) {
            try {
                let state = JSON.parse(atob(hash));
                Object.assign(this.state, {
                    id: state.i,
                    step: state.s,
                    owner: state.o,
                    status: state.t,
                    customer: state.c,
                    different: state.d,
                    filterState: state.f,
                    provision_mode: state.p
                });
            } catch {
                window.history.replaceState(null, '', window.location.pathname);
            }
        }
        
        if (this.state.filterState) {
            this.filterState.state = this.state.filterState;
        }

        this._onChangeStep(this.state.step, { init: true });
    },

    _startToggles: function() {
        this._bindWizardToggle();
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);

            this._parseAds();
            this._startState();
            this._initializePagination();
            this._startToggles();
            this._bindFilterEvents();
            this._initInsuranceModal();

            $('.escrow-ad-wrapper').removeClass('d-none');
            framework.hideLoading();
            setTimeout(() => $('div.o_loading').addClass('transparent'), 2000);
        });
    },

    _onClickButtonLicenseSerialNoHelper: function (ev) {
        ev.stopPropagation();
        const $tooltip = this.$('.license-serial-tooltip');
        $tooltip.toggle();
    },

    _initInsuranceModal: function() {
        if (!this.insurance || !this.insurance.input) {
            return;
        }
        const $modal = $('#insuranceQuoteModal');
        if (!$modal.length) {
            return;
        }
        this.insurance.modal = $modal;
        this._clearInsuranceBrand();
    },

    _populateInsuranceSelect: function(field, options = [], placeholder = '', config = {}) {
        if (!field || !field.$ || !field.$.length) {
            return;
        }
        const data = (options || []).map((opt, index) => {
            if (typeof opt === 'string') {
                return { id: opt, text: opt };
            }
            return {
                id: opt.code ?? opt.id ?? opt.value ?? opt.key ?? `option-${index}`,
                text: opt.text ?? opt.label ?? opt.name ?? opt.description ?? opt.id ?? '',
            };
        }).filter(opt => opt.id);

        if (field.$.data('select2')) {
            field.$.select2('destroy');
        }

        field.$.empty();
        const placeholderOption = new Option(placeholder || '', '', true, true);
        $(placeholderOption).attr('disabled', true);
        field.$.append(placeholderOption);
        data.forEach(opt => {
            const option = new Option(opt.text, opt.id, false, false);
            field.$.append(option);
        });

        field.$.select2({
            placeholder: placeholder,
            width: '100%',
        });

        field.$.val('');
        field.$.prop('disabled', config.disabled !== undefined ? config.disabled : !data.length);
        field._skipNextValidation = true;
        field.$.trigger('change');
    },

    _clearInsuranceBrand: function() {
        this._populateInsuranceSelect(this.insurance.input.brand, [], _t('Select vehicle brand'), { disabled: true });
        this._clearInsuranceModel();
    },

    _clearInsuranceModel: function() {
        this._populateInsuranceSelect(this.insurance.input.model, [], _t('Select vehicle model'), { disabled: true });
    },

    _onInsuranceYearChange: function() {
        this.insurance.alert.error.$.addClass('d-none');
        const yearField = this.insurance.input.year;
        if (!yearField || !yearField.value) {
            this._clearInsuranceBrand();
            return;
        }
        if (yearField.validate()) {
            this._fetchInsuranceBrands();
        }
    },

    _onInsuranceBrandChange: function() {
        this.insurance.alert.error.$.addClass('d-none');
        this._clearInsuranceModel();
        if (this.insurance.input.brand.value) {
            this._fetchInsuranceModels();
        }
    },

    _fetchInsuranceBrands: function() {
        const yearField = this.insurance.input.year;
        if (!yearField) {
            return;
        }
        if (!yearField.value) {
            return;
        }
        if (!yearField.validate()) {
            return;
        }

        this._populateInsuranceSelect(this.insurance.input.brand, [], _t('Loading brands...'), { disabled: true });
        this.insurance.state.brandRequestId += 1;
        const requestId = this.insurance.state.brandRequestId;

        rpc.query({
            route: '/escrow/insurance/brands',
            params: {
                year: yearField.value,
            },
        }).then(result => {
            if (requestId !== this.insurance.state.brandRequestId) {
                return;
            }
            if (result && result.success) {
                const options = (result.data || []).map(opt => ({
                    id: opt.code || opt.id || opt.value,
                    text: opt.name || opt.label || opt.text || opt.id,
                })).filter(opt => opt.id);
                this.insurance.alert.error.$.addClass('d-none');
                this._populateInsuranceSelect(this.insurance.input.brand, options, _t('Select vehicle brand'), { disabled: !options.length });
                if (!options.length) {
                    this._showInsuranceError(_t('No brands returned for the selected criteria.'));
                }
            } else {
                this._clearInsuranceBrand();
                this._showInsuranceError(result && result.message ? result.message : _t('Unable to fetch vehicle brands. Please try again.'));
            }
        }).catch(() => {
            if (requestId !== this.insurance.state.brandRequestId) {
                return;
            }
            this._clearInsuranceBrand();
            this._showInsuranceError(_t('Unable to fetch vehicle brands. Please try again.'));
        });
    },

    _fetchInsuranceModels: function() {
        const yearField = this.insurance.input.year;
        const brandField = this.insurance.input.brand;
        if (!yearField || !brandField) {
            return;
        }
        if (!yearField.value || !brandField.value) {
            return;
        }

        this._populateInsuranceSelect(this.insurance.input.model, [], _t('Loading models...'), { disabled: true });
        this.insurance.state.modelRequestId += 1;
        const requestId = this.insurance.state.modelRequestId;

        rpc.query({
            route: '/escrow/insurance/models',
            params: {
                year: yearField.value,
                brand_code: brandField.value,
                brand_name: brandField.text,
            },
        }).then(result => {
            if (requestId !== this.insurance.state.modelRequestId) {
                return;
            }
            if (result && result.success) {
                const options = (result.data || []).map(opt => ({
                    id: opt.code || opt.id || opt.value,
                    text: opt.label || opt.name || opt.text || opt.id,
                })).filter(opt => opt.id);
                this.insurance.alert.error.$.addClass('d-none');
                this._populateInsuranceSelect(this.insurance.input.model, options, _t('Select vehicle model'), { disabled: !options.length });
                if (!options.length) {
                    this._showInsuranceError(_t('No models returned for the selected brand.'));
                }
            } else {
                this._clearInsuranceModel();
                this._showInsuranceError(result && result.message ? result.message : _t('Unable to fetch vehicle models. Please try again.'));
            }
        }).catch(() => {
            if (requestId !== this.insurance.state.modelRequestId) {
                return;
            }
            this._clearInsuranceModel();
            this._showInsuranceError(_t('Unable to fetch vehicle models. Please try again.'));
        });
    },

    _showInsuranceError: function(message) {
        if (!this.insurance || !this.insurance.alert || !this.insurance.error) {
            return;
        }
        this.insurance.alert.success.$.addClass('d-none');
        this.insurance.error.message.$.text(message || _t('An unexpected error occurred.'));
        this.insurance.alert.error.$.removeClass('d-none');
    },

    _resetInsuranceForm: function() {
        if (!this.insurance || !this.insurance.input) {
            return;
        }
        Object.keys(this.insurance.input).forEach(key => {
            const field = this.insurance.input[key];
            if (!field || !field.$) {
                return;
            }
            field.value = '';
            field.$.removeClass('is-valid is-invalid -error just-validate-error-field');
            field.$.closest('.form__group').find('.form__error-label, .just-validate-error-label').remove();
            if (field.$.data('select2')) {
                field.$.trigger('change');
            }
        });
        this._clearInsuranceBrand();
    },

    _initBroker: function () {
        const $container = this.$('.broker-rates-container');
        if (!$container.length) return;

        const dataset = $container[0].dataset || {};
        this.currency.decimal = parseInt(dataset.currencyDecimals || this.currency.decimal, 10);
        this.currency.symbol = dataset.currencySymbol || this.currency.symbol;
        this.currency.position = dataset.currencyPosition || this.currency.position;

        this.broker.container.$ = $container;
        this.broker.wrapper.$ = $container.find('[data-role="table-wrapper"]');
        this.broker.tabs.$ = $container.find('[data-role="type-tabs"]');
        this.broker.tables.$ = $container.find('[data-role="tables"]');
        this.broker.loading.$ = $container.find('[data-role="loading"]');
        this.broker.empty.$ = $container.find('[data-role="empty"]');
        this.broker.error.$ = $container.find('[data-role="error"]');
        this.broker.summary.$ = $container.find('[data-role="summary"]');
        this.broker.amount.$ = $container.find('[data-role="amount"]');
        this.broker.campaign.$ = $container.find('[data-role="campaign"]');
        this.broker.viewMode.$ = $container.find('[data-role="view-mode"]');
        this.broker.button.refresh.$ = $container.find('[data-role="refresh"]');

        if (dataset.defaultCampaign) {
            this.broker.campaign.$.val(dataset.defaultCampaign);
        }

        const hasCampaign = this.broker.campaign.$.find('option[value!=""]').length > 0;
        if (hasCampaign && this.broker.campaign.$.val()) {
            this._fetchBrokerRates();
        } else {
            this._showBrokerError(_t('No active campaign is linked to your account yet.'));
        }
    },

    _initializePagination: function() {
        this._applyFilters();
    },
    
    _onCategoryChange: function() {
        const categoryId = this.ad.input.category.value;
        if (!categoryId) {
            this._clearDynamicAttributes();
            return Promise.resolve();
        }
        
        const self = this;
        const params = { 
            category_id: categoryId,
            ad_id: this.state.id || null
        };
        
        return this._rpc({
            route: '/my/ad/category/attributes',
            params: params,
        }).then(function (result) {
            if (result && result.success) {
                self._renderDynamicAttributes(result.attributes);
                
                if (result.attribute_values && self.state.id) {
                    setTimeout(() => {
                        Object.keys(result.attribute_values).forEach(key => {
                            const attrMeta = self.ad.dynamicAttributes && self.ad.dynamicAttributes[key];
                            if (attrMeta) {
                                const value = result.attribute_values[key];
                                const $input = attrMeta.$element;
                                
                                if (attrMeta.type === 'binary' && attrMeta.filePond && value) {
                                    let fileSource = value;
                                    if (fileSource.startsWith('data:')) {
                                        try {
                                            const parts = fileSource.split(',');
                                            if (parts.length === 2) {
                                                const payload = parts[1];
                                                const decoded = atob(payload);
                                                fileSource = 'data:image/png;base64,' + decoded;
                                            }
                                        } catch (e) {
                                            console.warn('Failed to check double encoding:', e);
                                        }
                                    }
                                    if (fileSource.startsWith('data:image') || fileSource.startsWith('http')) {
                                        attrMeta.filePond.addFile(fileSource).catch(err => {
                                            console.error('Could not load image to FilePond:', err);
                                        });
                                    }
                                } else if (attrMeta.type === 'boolean') {
                                    $input.find('input[type="checkbox"]').prop('checked', value === true);
                                } else if (attrMeta.type !== 'binary' && $input && $input.length && value !== null && value !== undefined) {
                                    $input.val(value);
                                }
                            }
                        });
                    }, 50);
                }
            } else {
                self._clearDynamicAttributes();
            }
        }).catch(function(error) {
            console.error('Error loading category attributes:', error);
            self._clearDynamicAttributes();
        });
    },
    
    _clearDynamicAttributes: function() {
        const $container = $('#dynamicAttributesContainer');
        const $panel = $('#dynamicAttributesPanel');
        
        if ($container.length) {
            $container.empty();
        }
        if ($panel.length) {
            $panel.hide();
        }
        if (this.ad && this.ad.dynamicAttributes) {
            this.ad.dynamicAttributes = {};
        }
    },
    
    _renderDynamicAttributes: function(attributes) {
        const $container = $('#dynamicAttributesContainer');
        const $panel = $('#dynamicAttributesPanel');
        
        if (!$container.length) {
            return;
        }
        
        $container.empty();
        
        if (!attributes || attributes.length === 0) {
            $panel.hide();
            return;
        }
        
        $panel.show();
        this.ad.dynamicAttributes = {};
        
        const html = qweb.render('escrow.dynamic.attributes', {
            attributes: attributes
        });
        
        $container.html(html);
        
        attributes.forEach(attr => {
            const $element = $container.find(`#attr_${attr.technical_name}`);
            this.ad.dynamicAttributes[attr.technical_name] = {
                id: attr.id,
                type: attr.attribute_type,
                required: attr.required,
                $element: $element
            };
            
            if (attr.mask && $element.length && attr.attribute_type !== 'binary' && attr.attribute_type !== 'boolean') {
                try {
                    let maskOption = attr.mask;
                    let maskConfig = {};

                    if (maskOption.startsWith('/') && maskOption.endsWith('/')) {
                        maskConfig = {
                            mask: new RegExp(maskOption.slice(1, -1)),
                            prepare: (str) => str.toUpperCase()
                        };
                    } else if (maskOption.startsWith('[') || maskOption.startsWith('{')) {
                        try {
                            const parsedConf = JSON.parse(maskOption);
                            maskConfig = parsedConf;
                            if (Array.isArray(maskConfig)) {
                                maskConfig.forEach(m => {
                                    if (!m.prepare) m.prepare = (str) => str.toUpperCase();
                                });
                                maskConfig = { mask: maskConfig };
                            } else {
                                if (!maskConfig.prepare) maskConfig.prepare = (str) => str.toUpperCase();
                            }
                        } catch (jsonErr) {
                            console.error('Invalid JSON mask:', jsonErr);
                            maskConfig = { mask: maskOption, prepare: (str) => str.toUpperCase() };
                        }
                    } else {
                        maskConfig = {
                            mask: maskOption,
                            prepare: (str) => str.toUpperCase(),
                            definitions: {
                                'a': /[A-Za-z]/,
                                '*': /[A-Za-z0-9]/
                            }
                        };
                    }
                    
                    IMask($element[0], maskConfig);
                } catch (e) {
                    console.error('Error applying mask:', e);
                }
            }
            
            if (attr.attribute_type === 'binary') {
                const inputElement = $element[0];
                if (inputElement) {
                    const pond = FilePond.create(inputElement, {
                        name: 'fileLicence',
                        allowMultiple: false,
                        accept: 'image/*',
                        maxFileSize: '15MB',
                        credits: false,
                        labelIdle: `<svg class="w-100" width="42" height="42" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M31.4998 33.2514C30.5318 33.2514 29.7484 32.468 29.7484 31.5C29.7484 30.532 30.5318 29.7486 31.4998 29.7486C35.3594 29.7486 38.5012 26.6068 38.5012 22.7473C38.5012 19.0723 35.626 16.0084 31.9592 15.7705L30.9256 15.709L30.4867 14.7779C28.7559 11.1152 25.0316 8.74863 20.9998 8.74863C16.968 8.74863 13.2438 11.1152 11.5129 14.7779L11.074 15.709L10.0445 15.7746C6.37363 16.0125 3.50254 19.0764 3.50254 22.7514C3.50254 26.6109 6.64434 29.7527 10.5039 29.7527C11.4719 29.7527 12.2553 30.5361 12.2553 31.5041C12.2553 32.4721 11.4719 33.2555 10.5039 33.2555C4.7125 33.2555 0.00390625 28.5469 0.00390625 22.7555C0.00390625 17.5834 3.79785 13.2193 8.80996 12.4031C11.2709 8.02676 15.9508 5.25 20.9998 5.25C26.0488 5.25 30.7287 8.02676 33.1938 12.3949C38.2059 13.2111 41.9998 17.5793 41.9998 22.7514C41.9998 28.5387 37.2912 33.2514 31.4998 33.2514Z" fill="black"/>
                                <path d="M26.2502 32.3737C25.8032 32.3737 25.3561 32.2014 25.0116 31.861L21.0002 27.8497L16.9889 31.861C16.3081 32.5459 15.1965 32.5459 14.5157 31.861C13.8307 31.176 13.8307 30.0686 14.5157 29.3877L19.7657 24.1377C20.4465 23.4528 21.5581 23.4528 22.2389 24.1377L27.4889 29.3877C28.1739 30.0727 28.1739 31.1801 27.4889 31.861C27.1444 32.2055 26.6973 32.3737 26.2502 32.3737Z" fill="#2414D8"/>
                                <path d="M21.0004 39.375C20.0324 39.375 19.249 38.5916 19.249 37.6236V25.3764C19.249 24.4084 20.0324 23.625 21.0004 23.625C21.9684 23.625 22.7518 24.4084 22.7518 25.3764V37.6277C22.7518 38.5916 21.9684 39.375 21.0004 39.375Z" fill="#2414D8"/>
                            </svg>
                            <span class="text-600">Select Image or Take New</span>
                            <div class="text-600">No Image Selected</div>`,
                    });
                    
                    this.ad.dynamicAttributes[attr.technical_name].filePond = pond;
                    
                    pond.on('addfile', () => {
                        const $formGroup = $element.closest('.form__group');
                        $formGroup.find('.form__error-label, .just-validate-error-label').remove();
                        $element.removeClass('is-invalid -error just-validate-error-field');
                    });
                }
            }
            
            $element.on('input change', function() {
                const $formGroup = $element.closest('.form__group');
                $formGroup.find('.form__error-label, .just-validate-error-label').remove();
                $element.removeClass('is-invalid -error just-validate-error-field');
            });
            
            if (attr.technical_name === 'brand' && attr.attribute_type === 'many2one') {
                $element.on('change', () => {
                    const brandId = $element.val();
                    const $modelSelect = $container.find('#attr_model');
                    
                    if (!brandId || !$modelSelect.length) return;
                    
                    this._rpc({
                        route: '/my/ad/brand/models',
                        params: { brand_id: parseInt(brandId, 10) },
                    }).then((result) => {
                        if (result && result.success) {
                            $modelSelect.empty();
                            $modelSelect.append('<option value="">-- Seçiniz --</option>');
                            result.models.forEach(model => {
                                $modelSelect.append(`<option value="${model.id}">${model.name}</option>`);
                            });
                        }
                    });
                });
            }
        });
    },
    
    _getDynamicAttributeValues: async function() {
        if (!this.ad.dynamicAttributes) {
            return [];
        }
        
        const attributeValues = [];
        
        for (const [technicalName, attrMeta] of Object.entries(this.ad.dynamicAttributes)) {
            const $el = attrMeta.$element;
            let value;
            
            if (attrMeta.type === 'boolean') {
                value = $el.find('input[type="checkbox"]').is(':checked');
            } else if (attrMeta.type === 'binary') {
                const filePondInstance = attrMeta.filePond;
                if (filePondInstance) {
                    const files = filePondInstance.getFiles();
                    if (files && files.length > 0) {
                        try {
                            const fileItem = files[0];
                            const file = fileItem.file;
                            
                            value = await new Promise((resolve, reject) => {
                                const reader = new FileReader();
                                reader.onload = (e) => {
                                    const base64String = e.target.result;
                                    const base64Data = base64String.split(',')[1];
                                    resolve(base64Data);
                                };
                                reader.onerror = reject;
                                reader.readAsDataURL(file);
                            });
                        } catch (err) {
                            console.error('Error reading file:', err);
                            value = null;
                        }
                    } else {
                        value = null;
                    }
                } else {
                    value = $el.val() || $el.data('file-uploaded');
                }
            } else if (attrMeta.type === 'many2one') {
                const selectedValue = $el.val();
                value = selectedValue ? parseInt(selectedValue, 10) : null;
            } else if (attrMeta.type === 'integer') {
                const intValue = $el.val();
                value = intValue ? parseInt(intValue, 10) : null;
            } else if (attrMeta.type === 'float') {
                const floatValue = $el.val();
                value = floatValue ? parseFloat(floatValue) : null;
            } else {
                value = $el.val();
            }
            
            if (attrMeta.required && !value && value !== false) {
                continue;
            }
            
            if (value !== '' && value !== null && value !== undefined) {
                attributeValues.push({
                    attribute_id: attrMeta.id,
                    value: value
                });
            }
        }
        
        return attributeValues;
    },
    
    _onFieldValid: function(field, valid, message='') {
        const $group = field.$.closest('.form__group');
        $group.find('.form__error-label, .just-validate-error-label').remove();
        field.$.removeClass('is-valid is-invalid -error just-validate-error-field');

        if (field._skipNextValidation) {
            field._skipNextValidation = false;
            return;
        }

        if (valid) {
            field.$.addClass('is-valid');
        } else {
            field.$.addClass('is-invalid -error just-validate-error-field');
            field.$.closest('.form__group').append($(`<div class="form__error-label just-validate-error-label">${message}</div>`));
        }
    },

    _onVinComplete: function(vin) {
        const self = this;
        this._rpc({
            route: '/my/ad/vin/check',
            params: { vin: vin },
        }).then(function (result) {;
            if (result && result.success) {
                if (result.data) {
                    if (result.data.brand_id) {
                        self.ad.input.brand.value = result.data.brand_id;
                        self.ad.input.brand.$.trigger('change');
                    }
                }
            }
        }).catch(function () {
        });
    },

    _formatIbanDisplay: function(iban) {
        if (!iban) return '';
        const cleanIban = iban.replace(/\s/g, '').toUpperCase();
        
        if (cleanIban.length >= 4) {
            let formatted = cleanIban.substring(0, 4);
            for (let i = 4; i < cleanIban.length; i += 4) {
                formatted += ' ' + cleanIban.substring(i, i + 4);
            }
            return formatted;
        }
        return cleanIban;
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

    _isOtpValidate: async function(field) {
        if (field.value.length === 10) {
            let otp = field._.masked.value;
            let result = await this._rpc({
                route: '/my/otp/validate',
                params: { otp },
            });
            if (result) {
                this._showFieldSuccessIcon(field);
                return result;
            }
        } 
        this._hideFieldIcon(field);
    },

    _isIbanVerified: async function(ibanField, vatField) {
        let vat = vatField._.masked.value;
        let iban = ibanField._.masked.value;
        if (this._isIbanValid(iban)) {
            let result = await this._rpc({
                route: '/my/iban/verify',
                params: { iban, vat },
            });
            if (result) {
                this._showFieldSuccessIcon(ibanField);
                return result;
            }
        }
        this._hideFieldIcon(ibanField);
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
        $icon.removeClass('fa-exclamation-circle fa-check-circle fa-spinner fa-spin');
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

    _onToggleVehicleHolder: function() {
        const id = this.state.id;
        if (this.values.ads[id].sale_state === 'waiting_official_sale_img' || this.values.ads[id].sale_state === 'waiting_transfer_approval' || this.values.ads[id].sale_state === 'transferred') {
            this.state.status = 'success';
            this._onChangeStep(5);
        } else {
            this.state.item_id = this.values.ads[id].item_id;
            if (id) {
                this._openSellerEditForCard(id, 'vehicle');
            }
        }
    },

    _onToggleSellerHolder: function() {
        const id = this.state.id;
        if (this.values.ads[id].sale_state === 'waiting_official_sale_img' || this.values.ads[id].sale_state === 'waiting_transfer_approval' || this.values.ads[id].sale_state === 'transferred') {
            this.state.status = 'success';
            this._onChangeStep(5);
        } else {
            if (id) {
                this._openSellerEditForCard(id, 'seller');
            }
        }
    },

    _openSellerEditForCard: function(id, section) {
        this._closeSidebar();
        if (section === 'seller') {
            this._onChangeStep(1);
        } else if (section === 'vehicle') {
            this._onChangeStep(2);
        }
    },

    _parseAds: function () {
        this.values.ads = {};
        $('[field="ad.item"][data-value]').each((i, e) => {
            const $this = $(e);
            const values = $this.data('value');
            this.values.ads[e.dataset.id] = {
                img: $this.find('.escrow-ad-item-image img').attr('src'),
                name: $this.find('.escrow-ad-item-name').text().trim(),
                price: $this.find('.escrow-ad-item-price').data('value'),
                ...values
            };
            $this.data('value', null);
            $this.attr('data-value', null);
        });
    },

    _deleteAds: function (id) {
        delete this.values.ads[id];
        this.ad.item.$.filter(`[data-id=${id}]`).remove();
    },

    _onClickButtonSidebarToggle: function (ev) {
        $('.escrow-ad-wrapper').toggleClass('blur');
        $('.escrow-ad-sidebar-section').addClass('d-none');
        this.ad.sideback.$.toggleClass('d-none');
        this.ad.sidebar.$.toggleClass('show');

        const value = ev?.currentTarget?.dataset?.value;
        if (value) {
            $(`.escrow-ad-sidebar-${value}`).removeClass('d-none');
        }
    },

    _activateView: function (view) {
        const views = ['form', 'grid', 'list'];
        let current = views.find(v => this.ad.button[v].$.hasClass('active'));
        if (!current) {
            if ($('.escrow-ad-edit').is(':visible')) {
                current = 'form';
            } else if (this.ad.view.grid.$.is(':visible')) {
                current = 'grid';
            } else {
                current = 'list';
            }
        }

        if (current === view) {
            return;
        }

        this.ad.button.list.$.removeClass('active');
        this.ad.button.grid.$.removeClass('active');
        if (view !== 'form') {
            this.ad.button[view].$.addClass('active');
        }
        const showRead = view !== 'form';
        const $read = $('.escrow-ad-read');
        const $edit = $('.escrow-ad-edit');

        if (showRead) {
            this.ad.view.form.$.stop(true, true).hide();
            if (view === 'list') {
                this.ad.view.grid.$.stop(true, true).hide();
                this.ad.view.list.$.stop(true, true).fadeIn(400, () => {
                    this._applyFilters();
                });
            } else {
                this.ad.view.list.$.stop(true, true).hide();
                this.ad.view.grid.$.stop(true, true).fadeIn(400, () => {
                    this._applyFilters();
                });
            }
            $edit.stop(true, true).fadeOut(400, () => {
                $read.stop(true, true).fadeIn(400);
            });
        } else {
            this.ad.view.list.$.stop(true, true).hide();
            this.ad.view.grid.$.stop(true, true).hide();
            $read.stop(true, true).fadeOut(400, () => {
                this.ad.view.form.$.stop(true, true).fadeIn(400);
                $edit.stop(true, true).fadeIn(400);
            });
        }
    },

    _onClickButtonList: function () {
        this._activateView('list');
    },

    _onClickButtonGrid: function () {
        this._activateView('grid');
    },

    _onClickButtonForm: function () {
        this._activateView('form');
    },

    _onClickButtonCreate: function (ev) {
        Object.assign(this.state, { id: 0, owner: 0, customer: 0, item_id: 0 });
        this._resetDynamicAttributes();
        this._resetWaitingWizardForm();
        this._onChangeStep(1);
    },

    _resetDynamicAttributes: function() {
        if (!this.state.id) {
            this._clearDynamicAttributes();
        }
    },

    _resetWaitingWizardForm: function() {
        const $step1 = $('.wizard-step-1');
        $step1.find('.approval-waiting-msg').remove();
        $step1.children().removeClass('d-none');
    },

    _closeSidebar: function() {
        $('.escrow-ad-wrapper').removeClass('blur');
        $('.escrow-ad-sidebar-section').addClass('d-none');
        this.ad.sideback.$.addClass('d-none');
        this.ad.sidebar.$.removeClass('show');
    },

    _prefillCustomerFromAd: function() {
        const $wiz = $('.escrow-wizard');
        let customerId = this.state.customer;

        if (customerId) {
            this._rpc({
                route: '/my/partner/get',
                params: { partner_id: customerId }
            }).then((customerData) => {
                if (customerData.success) {
                    const customer = customerData.partner;
                    if (!customer.is_company) {
                        $wiz.find('input[name="customerUserType"][value="individual"]').prop('checked', true);
                        this._bindWizardToggle();
                        this.customer.input.name.value = customer.name || '';
                        this.customer.input.tc.value = customer.vat || '';
                        this.customer.input.phone_individual.value = customer.phone || '';
                        this.customer.input.email_individual.value = customer.email || '';
                        this.customer.input.address_individual.value = this._formatAddress(customer);
                        this._isOtpValidate(this.customer.input.phone_individual);
                    } else {
                        $wiz.find('input[name="customerUserType"][value="corporate"]').prop('checked', true);
                        this._bindWizardToggle();
                        this.customer.input.corporate_title.value = customer.name || '';
                        this.customer.input.tax_number.value = customer.vat || '';
                        this.customer.input.tax_office.value = customer.commercial_partner_id?.name || '';
                        this.customer.input.corporate_person.value = customer.name || '';
                        this.customer.input.address_corporate.value = this._formatAddress(customer);
                        this.customer.input.phone_corporate.value = customer.phone || '';
                        this.customer.input.email_corporate.value = customer.email || '';
                        this._isOtpValidate(this.customer.input.phone_corporate);
                    }
                }
            });
        }
    },

    _prefillSellerFromAd: function() {
        const $wiz = $('.escrow-wizard');

        let ownerId = this.state.owner;
        if (ownerId) {
            this._rpc({
                route: '/my/partner/get',
                params: { partner_id: ownerId }
            }).then((ownerData) => {
                if (ownerData.success) {
                    const owner = ownerData.partner;
                    if (owner.is_company) {
                        $wiz.find('input[name="userType"][value="corporate"]').prop('checked', true);
                        this._bindWizardToggle();
                        this.seller.input.corporate_title.value = owner.name || '';
                        this.seller.input.tax_number.value = owner.vat || '';
                        this.seller.input.corporate_person.value = owner.name || '';
                        this.seller.input.city_corporate.value = owner.city || '';
                        this.seller.input.phone_corporate.value = owner.phone || '';
                        this.seller.input.email_corporate.value = owner.email || '';
                        this._isOtpValidate(this.seller.input.phone_corporate);
                        if (owner.bank_ids && owner.bank_ids.length > 0) {
                            const bankAccount = owner.bank_ids.at(-1);
                            this.seller.input.iban_corporate.value = this._formatIbanDisplay(bankAccount.acc_number);
                            this.seller.input.iban_name_corporate.value = bankAccount.api_merchant || owner.name;
                            this._isIbanVerified(this.seller.input.iban_corporate, this.seller.input.tax_number);
                        }
                    } else {
                        $wiz.find('input[name="userType"][value="individual"]').prop('checked', true);
                        this._bindWizardToggle();
                        this.seller.input.name.value = owner.name || '';
                        this.seller.input.tc.value = owner.vat || '';
                        this.seller.input.phone_individual.value = owner.phone || '';
                        this.seller.input.email_individual.value = owner.email || '';
                        this.seller.input.city_individual.value = owner.city || '';
                        this._isOtpValidate(this.seller.input.phone_individual);
                        if (owner.bank_ids && owner.bank_ids.length > 0) {
                            const bankAccount = owner.bank_ids[0];
                            this.seller.input.iban_individual.value = this._formatIbanDisplay(bankAccount.acc_number);
                            this.seller.input.iban_name_individual.value = bankAccount.api_merchant || owner.name;
                            this._isIbanVerified(this.seller.input.iban_individual, this.seller.input.tc);
                        }
                    }
                }
                return Promise.resolve();
            }).catch((e) => {
                console.warn('Could not load owner data for prefill form', e);
            });
        }
        $wiz.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $wiz.find('.form__error-label, .just-validate-error-label').remove();
    },

    _loadSellerInfoForSidebar: function(adId, ownerId) {
        const self = this;
        const $wiz = $('.escrow-wizard');
        
        this._rpc({
            route: '/my/partner/get',
            params: { partner_id: ownerId }
        }).then((ownerData) => {
            if (ownerData.success && self.values.ads[adId]) {
                const owner = ownerData.partner;

                self.values.ads[adId].seller_name = owner.name || 'Not Specified';
                self.values.ads[adId].seller_tc = owner.vat || 'Not Specified';
                self.values.ads[adId].seller_city = owner.city || 'Not Specified';

                if (owner.bank_ids && owner.bank_ids.length > 0) {
                    const bankAccount = owner.bank_ids[0];
                    self.values.ads[adId].seller_iban = self._formatIbanDisplay(bankAccount.acc_number) || 'Not Specified';
                } else {
                    self.values.ads[adId].seller_iban = 'Not Specified';
                }
                const $item = $('.escrow-ad-sidebar-items');
                if ($item.length && $('.escrow-ad-button-edit').data('id') == adId) {
                    $item.find('.seller-name').text(self.values.ads[adId].seller_name);
                    $item.find('.seller-tc').text(self.values.ads[adId].seller_tc);
                    $item.find('.seller-city').text(self.values.ads[adId].seller_city);
                    $item.find('.seller-iban').text(self.values.ads[adId].seller_iban);
                }
            }
        }).catch(() => {
            console.warn('Could not load seller data for sidebar');
        });
        $wiz.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $wiz.find('.form__error-label, .just-validate-error-label').remove();
    },

    _prefillProductFromAd: function() {
        const adData = this.values.ads[this.state.id];
        if (!adData) return;

        if (adData.price) {
            this.ad.input.price.value = format.float(adData.price);
        }
    },

    _formatAddress: function(partner) {
        const parts = [];
        if (partner.street) parts.push(partner.street);
        if (partner.street2) parts.push(partner.street2);
        if (partner.city) parts.push(partner.city);
        if (partner.state_id && partner.state_id.name) parts.push(partner.state_id.name);
        if (partner.country_id && partner.country_id.name) parts.push(partner.country_id.name);
        return parts.join(', ');
    },

    _parsePrice: function(priceStr) {
        if (!priceStr) return 0;
        const str = String(priceStr);
        const cleaned = str.replace(/\./g, '').replace(',', '.');
        const parsed = parseFloat(cleaned);
        return isNaN(parsed) ? 0 : parsed;
    },

    _saveAdData: async function() {
        const attributes = await this._getDynamicAttributeValues();
        
        let params = {
            id: this.state.id,
            category_id: parseInt(this.ad.input.category.$.val(), 10) || null,
            price: this._parsePrice(this.ad.input.price.value),
            owner_id: this.state.owner || null,
            attributes: attributes,
        };

        return rpc.query({ route: '/my/ad/save', params }).then((result) => {
            if ('error' in result) {
                throw new Error(result.error);
            }
            return result;
        });
    },

    _onClickButtonDelete: function (ev) {
        const id = parseInt($(ev.currentTarget).data('id'));
        const popup = new dialog(this, {
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
                    framework.showLoading();
                    rpc.query({ route: '/my/ad/delete', params: { id } }).then((result) => {
                        if ('error' in result) {
                            this.displayNotification({
                                type: 'warning',
                                title: _t('Warning'),
                                message: _t('An error occured.') + ' ' + result.error,
                            });
                        } else {
                            this._deleteAds(id);
                            this._activateView('list');
                            this.displayNotification({
                                type: 'success',
                                title: _t('Success'),
                                message: _t('Ad has been removed.'),
                            });
                        }
                    }).guardedCatch(() => {
                        this.displayNotification({
                            type: 'danger',
                            title: _t('Error'),
                            message: _t('An error occured. Please contact with your system administrator.'),
                        });
                    }).finally(() => {
                        popup.destroy();
                        framework.hideLoading();
                    });
                },
            }],
        });
        popup.open();
    },

    _onClickAd: function (ev) {
        this._onClickButtonSidebarToggle({ currentTarget: { dataset: { value: 'items'}}});

        const id = ev?.currentTarget?.dataset?.id;

        this.state.id = id ? parseInt(id, 10) : 0;
        this.state.owner = this.values.ads[id]?.owner_id || 0;
        this.state.customer = this.values.ads[id]?.customer_id || 0;

        const value = this.values.ads[id];
        const $item = $('.escrow-ad-sidebar-items');
        if ($item.length) {
            $item.find('.escrow-ad-item-name').text(value.name);
            $item.find('.escrow-ad-item-categ').text(value.category_name || value.categ);
            $item.find('.seller-name').text(value.partner || 'Not specified');
            $item.find('.seller-tc').text(value.vat || 'Not specified');
            $item.find('.seller-city').text(value.city || 'Not specified');
            $item.find('.seller-iban').text(value.iban || 'Not specified');
            
            const $attrContainer = $item.find('.escrow-ad-attributes-container');
            $attrContainer.empty();
            if (value.attributes && value.attributes.length > 0) {
                value.attributes.forEach(attr => {
                    $attrContainer.append(`
                        <div class="info-item">
                            <span class="info-label">${attr.name}:</span>
                            <span class="info-value">${attr.value}</span>
                        </div>
                    `);
                });
            }

            let stateClass = 'secondary', stateLabel = '';
            const state = value.raw_state;
            const saleState = value.sale_state;

            if (state === 'draft') {
                stateClass = 'secondary';
                stateLabel = _t('Draft');
            } else if (state === 'waiting') {
                stateClass = 'warning';
                stateLabel = _t('Waiting Approval');
            } else if (state === 'new' && !saleState) {
                stateClass = 'success';
                stateLabel = _t('Published');
            } else if (state === 'sold') {
                stateClass = 'dark';
                stateLabel = _t('Sold');
            } else if (state === 'cancelled') {
                stateClass = 'danger';
                stateLabel = _t('Cancelled');
            } else if (saleState === 'waiting_payment') {
                stateClass = 'info';
                stateLabel = _t('Waiting Payment');
            } else if (saleState === 'waiting_official_doc') {
                stateClass = 'info';
                stateLabel = _t('Waiting Official Doc');
            } else if (saleState === 'waiting_transfer') {
                stateClass = 'primary';
                stateLabel = _t('Waiting Transfer');
            } else if (saleState === 'transferred') {
                stateClass = 'success';
                stateLabel = _t('Transferred');
            }

            $item.find('.escrow-ad-item-state').html(`<span class="badge badge-${stateClass}">${stateLabel}</span>`);
            $item.find('.escrow-ad-item-price').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
        } else {
            $item.find('.seller-name, .seller-tc, .seller-iban, .seller-city').text('Not specified');
            $item.find('.escrow-ad-attributes-container').empty();
            $item.find('.escrow-ad-item-price').text('');
            $item.find('.escrow-ad-item-state').html('');
            $item.find('.escrow-ad-item-name').text(_t('No ad found'));
            $item.find('.escrow-ad-item-categ').text('');
        }
    },
    
    _onClickWizardClose: function () {
        this._onChangeStep(this.wizard.currentStep - 1);
    },

    _onInputAmount: function (ev) {
        this._onClickInstallmentRow();
    },

    _onClickInstallmentRow: function () {
        const $el = $('[field="installment.row"] .installment-selected');
        const value = $el.data('value') || 0;
        this.payment.amount.paid.$.text(format.currency(value, this.currency.position, this.currency.symbol, this.currency.decimal));
    },

    _onChangeStep: function (step, options={}) {
        if (step < 0 || step > 5) {
            return;
        }

        if (step === 0) {
            this._resetProvisionWarning();
            Object.assign(this.state, { id: 0, owner: 0 });
            this.seller.wizard.$.fadeOut(200, () => {
                $('.header').removeClass('header__steps');
                this.seller.ads.$.fadeIn(200);
            });
        } else { 
            $('.header').addClass('header__steps');
            this.wizard.previousStep = this.wizard.currentStep;
            this.wizard.currentStep = step;
            this._ensureWizardVisible();
            this._updateStepHeaders(step, options);
            this._showStepContent(step);
            this._handleStepSpecificActions(step, options);

            if (this.state.provision_mode) {
                this._showProvisionWarning();
            }
        }

        if (this.ad.sidebar.$.hasClass('show')) {
            this._onClickButtonSidebarToggle();
        }

        this._setState({ step });
    },

    _showProvisionWarning: function() {
        const $headerSteps = $('.escrow-wizard-header:visible');
        const $wizardSteps = $('.escrow-wizard .steps:visible');
        const $fallbackSteps = $('.header .steps:visible').first();
        const $target = $headerSteps.length ? $headerSteps : ($wizardSteps.length ? $wizardSteps : $fallbackSteps);

        if (!$target.length) {
            return;
        }

        if ($target.css('position') === 'static') {
            $target.css('position', 'relative');
        }

        if ($target.find('.provision-warning').length === 0) {
            $target.append(qweb.render('paylox.escrow.provision.warning'));
        }
    },

    _hideProvisionWarning: function() {
        $('.provision-warning').remove();
    },

    _resetProvisionWarning: function() {
        this._hideProvisionWarning();
        if (this.state.provision_mode) {
            this._setState({ provision_mode: false });
        }
    },

    _ensureWizardVisible: function() {
        this.seller.ads.$.fadeOut(200, () => {
            this.seller.wizard.$.fadeIn(200);
        });
    },

    _updateStepHeaders: function(stepNumber, options) {
        const $steps = $('.steps__item');
        
        $steps.each(function(index) {
            const $step = $(this);
            const currentStepNum = index + 1;
            
            $step.removeClass('-active -completed completed active');
            
            if (currentStepNum < stepNumber) {
                $step.addClass('-completed completed');
            } else if (currentStepNum === stepNumber) {
                $step.addClass('-active active');
                if (options.markAsCompleted) {
                    $step.addClass('-completed completed');
                }
            }
        });
    },

    _showStepContent: function(stepNumber) {
        const $steps = $('.wizard-step');
        const $targetStep = $(`.wizard-step-${stepNumber}`);
        if ($targetStep.is(':visible')) {
            return;
        }
        $steps.stop(true, true);
        const $currentStep = $steps.filter(':visible');
        
        if ($currentStep.length === 0) {
            $steps.hide();
            $targetStep.fadeIn(300);
        } else {
            $currentStep.fadeOut(250, () => {
                $targetStep.fadeIn(250);
            });
        }
    },

    _handleStepSpecificActions: function(stepNumber) {
        switch(stepNumber) {
            case 1:
                this._resetProvisionWarning();
                this._resetWaitingWizardForm();
                if (!this.state.id && !this.state.owner) {
                    for (const input of Object.values(this.seller.input)) {
                        input.value = null;
                        this._hideFieldIcon(input);
                    }
                } else {
                    this._initializeSellerInfoForm();
                }
                break;
                
            case 2:
                this._initializeProductInfoForm();
                break;
                
            case 3:
                this._initializeCustomerInfoForm();
                break;
                
            case 4:
                this._initializePaymentForm();
                break;
                
            case 5:
                this._initializeFinalStep();
        }
    },

    _onClickWizardSubmit: function() {
        const fileValue = this.payment.different.info.fileOfficialSale.value;
        let fileData = null;
        
        if (fileValue) {
            if (typeof fileValue === 'string') {
                const base64Match = fileValue.match(/^data:([^;]+);base64,(.+)$/);
                if (base64Match) {
                    fileData = {
                        data: base64Match[2],
                        mimetype: base64Match[1] || 'image/png' 
                    };
                } else {
                    fileData = {
                        data: fileValue,
                        mimetype: 'image/png'
                    };
                }
            } else if (typeof fileValue === 'object' && fileValue.data) {
                fileData = fileValue;
            }
        }
        
        this._rpc({
            route: '/payment/escrow/ad/official_sale',
            params: { 
                ad_id: this.state.id,
                file: fileData,
            }
        }).then((result) => {
            if (result && result.success) {
                this.displayNotification({
                    type: 'success',
                    title: 'Success',
                    message: 'Official sale document has been requested successfully.',
                });
                this.wizard.button.submit.$.attr('disabled', 'disabled').addClass('btn-secondary').removeClass('btn-primary');
                const $parent = this.payment.different.info.fileOfficialSale.$.closest('.form__group');
                $parent.removeClass('d-none');
            } else {
                this.displayNotification({
                    type: 'warning',
                    title: 'Error',
                    message: (result && result.error) || 'An error occurred while requesting official sale document.',
                });
            }
        }).catch((error) => {
            this.displayNotification({
                type: 'danger',
                title: 'Error',
                message: 'Connection error occurred.',
            });
            console.error('Error requesting official sale document:', error);
        });
    },

    _initializeFinalStep: function() {
        this._rpc({
            route: '/payment/escrow/transaction-data',
            params: { 
                product_id: this.state.id,
                status: this.state.status
            }
        }).then((result) => {
            if (result && !result.error) {
                const templateData = {
                    total_amount: result.total_amount || 0,
                    previous_amount: result.previous_amount || 0,
                    remaining_amount: result.remaining_amount || 0,
                    transactions: result.transactions || [],
                    paid: result.paid || false,
                    currency: this.currency,
                    format: format,
                    state: this.state.status,
                };
                const $rendered = $(qweb.render('paylox.escrow.transaction.item', templateData));

                const $container = $('.completion-content');
                if ($container.length) {
                    $container.empty().append($rendered);
                    this._initializeFileUploads(result.transactions || []);
                }
                if (result.paid > 0) {
                    this.payment.transaction.status.html = 'Success';
                    this.payment.transaction.status.$.addClass('text-success');
                    this.payment.transaction.date.html = result.paid_date;
                    if (!result.img) {
                        const $buttonParent = this.wizard.button.submit.$.closest('.completion-actions');
                        $buttonParent.removeClass('d-none');
                        const $parent = this.payment.different.info.fileOfficialSale.$.closest('.form__group');
                        $parent.removeClass('d-none');
                        this.wizard.button.close.$.addClass('d-none');
                    } else {
                        this.wizard.button.submit.$.attr('disabled', 'disabled').addClass('btn-secondary').removeClass('btn-primary');
                        const $parent = this.payment.different.info.fileOfficialSale.$.closest('.form__group');
                        $parent.removeClass('d-none');
                        this.payment.different.info.fileOfficialSale.value = result.img;
                        this.wizard.button.close.$.addClass('d-none');
                    }
                } else {
                    this.payment.transaction.status.html = 'Pending';
                    this.payment.transaction.status.$.addClass('text-warning');
                    this.payment.transaction.date.html = '-';
                }
                if (result.different){
                    this._setState({ different: true });
                }
            } else {
                console.error('Error loading transaction data:', result && result.error);
            }
        }).catch(function(error) {
            console.error('Error loading transaction data:', error);
        });
    },

    _setCookie: function (name, value, days=1) {
        let date = new Date(); date.setTime(date.getTime() + (days*24*60*60*1000));
        let expires = '; expires=' + date.toUTCString();
        document.cookie = `${name}=${encodeURIComponent(value)}${expires}; path=/`;
    },

    _setState: function (value={}) {
        if ('id' in value) {
            this.state.id = value.id;
        }
        if ('step' in value) {
            this.state.step = value.step;
        }
        if ('owner' in value) {
            this.state.owner = value.owner;
        }
        if ('status' in value) {
            this.state.status = value.status;
        }
        if ('different' in value) {
            this.state.different = value.different;
        }
        if ('filterState' in value) {
            this.state.filterState = value.filterState;
        }
        if ('provision_mode' in value) {
            this.state.provision_mode = value.provision_mode;
        }

        let values = {
            i: this.state.id,
            s: this.state.step,
            o: this.state.owner,
            t: this.state.status,
            c: this.state.customer,
            d: this.state.different,
            f: this.state.filterState,
            p: this.state.provision_mode,
        }
        let hash = btoa(JSON.stringify(values));
        let url = new URL(window.location); url.searchParams.set('', hash);
        window.history.replaceState({'': hash}, '', url);
    },

    _disableWizard: function() {
        this.wizard.loading.$.addClass('show');
        this.seller.button.close.$.attr('disabled', 'disabled');
    },

    _enableWizard: function() {
        this.wizard.loading.$.removeClass('show');
        this.seller.button.close.$.attr('disabled', null);
    },

    _nextStep: async function () {
        if (this.wizard.currentStep === 1) {
            for (const input of Object.values(this.seller.input)) {
                let valid = await input.validate();
                if (!valid) {
                    return this.displayNotification({
                        title: 'Error',
                        message: 'An error occurred while saving seller information.',
                        type: 'warning',
                    });
                }
            }

            this._disableWizard();
            this._saveSellerInfo().then((result) => {
                if (result.success && result.partner_id) {
                    this.state.owner = result.partner_id;
                    return this._startOtp(result.partner_id).then((otpRes) => {
                        if (otpRes && otpRes.success) {
                            this.wizard.otpId = otpRes.otp_id;
                            this._showOtpModal(otpRes.expires_in || 120, true);
                        } else if (otpRes && otpRes.is_otp_verified) {
                            this._markStepCompleted(this.wizard.currentStep);
                            this._onChangeStep(this.wizard.currentStep + 1);
                        } else {
                            this.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                        }
                    }).finally(() => {
                        this._enableWizard();
                    });

                } else {
                    if (result.state === false) {
                        if (result.provision_mode) {
                            this.state.provision_mode = true;
                            this._showProvisionWarning();
                            this.state.owner = result.partner_id;
                            return this._startOtp(result.partner_id).then((otpRes) => {
                                if (otpRes && otpRes.success) {
                                    this.wizard.otpId = otpRes.otp_id;
                                    this._showOtpModal(otpRes.expires_in || 120, true);
                                } else if (otpRes && otpRes.is_otp_verified) {
                                    this._markStepCompleted(this.wizard.currentStep);
                                    this._onChangeStep(this.wizard.currentStep + 1);
                                } else {
                                    this.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                                }
                            }).finally(() => {
                                this._enableWizard();
                            });
                        }
                        const $step1 = $('.wizard-step-1');
                        $step1.children().addClass('d-none');
                        if ($step1.find('.approval-waiting-msg').length === 0) {
                            $step1.append(qweb.render('paylox.escrow.approval.waiting'));
                        }
                    } else {
                        this.displayNotification({
                            type: 'danger',
                            title: 'Error',
                            message: result.message || 'An error occurred while saving seller information.',
                        });
                    }
                }
            }).catch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: 'Error',
                    message: 'Connection error occurred.',
                });
                console.error('Error saving seller info:', error);
            }).finally(() => {
                this._enableWizard();
            });
        }

        if (this.wizard.currentStep === 2) {
            this.ad.input.category.$.trigger('change');
            for (const input of Object.values(this.ad.input)) {
                let valid = await input.validate();
                if (!valid) {
                    return this.displayNotification({
                        title: 'Error',
                        message: 'Please fill in all required fields.',
                        type: 'warning',
                    });
                }
            }
            
            if (this.ad.dynamicAttributes) {
                for (const [technicalName, attrMeta] of Object.entries(this.ad.dynamicAttributes)) {
                    if (attrMeta.required) {
                        const $el = attrMeta.$element;
                        const $formGroup = $el.closest('.form__group');
                        const fieldLabel = $formGroup.find('label').text().trim() || 'Field';
                        let value;
                        let valid = true;
                        
                        if (attrMeta.type === 'boolean') {
                            value = $el.find('input[type="checkbox"]').is(':checked');
                        } else if (attrMeta.type === 'binary') {
                            const filePondInstance = attrMeta.filePond;
                            if (filePondInstance) {
                                const files = filePondInstance.getFiles();
                                value = files && files.length > 0;
                            } else {
                                value = $el.val() || $el.data('file-uploaded');
                            }
                        } else {
                            value = $el.val();
                        }
                        
                        if (!value && value !== false) {
                            valid = false;
                        }
                        
                        $formGroup.find('.form__error-label, .just-validate-error-label').remove();
                        if (!valid) {
                            $el.addClass('is-invalid -error just-validate-error-field').removeClass('is-valid');
                            $formGroup.append($(`<div class="form__error-label just-validate-error-label">${fieldLabel} is required</div>`));
                            return this.displayNotification({
                                title: 'Error',
                                message: 'Please fill in all required fields.',
                                type: 'warning',
                            });
                        } else {
                            $el.removeClass('is-invalid -error just-validate-error-field').addClass('is-valid');
                        }
                    }
                }
            }

            this._disableWizard();
            this._saveAdData().then((result) => {
                if (result.success || result.id) {
                    if (result.id) {
                        this.state.id = result.id;
                        this.state.item_id = result.item_id;
                    }
                    this._markStepCompleted(this.wizard.currentStep);
                    this._onChangeStep(this.wizard.currentStep + 1);
                } else {
                    this.displayNotification({
                        type: 'danger',
                        title: 'Error',
                        message: result.message || 'Product information could not be saved.',
                    });
                }
            }).catch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: 'Error',
                    message: 'Connection error occurred.',
                });
            }).finally(() => {
                this._enableWizard();
            });
            return false;
        }

        if (this.wizard.currentStep === 3) {
            for (const input of Object.values(this.customer.input)) {
                let valid = await input.validate();
                if (!valid) {
                    return this.displayNotification({
                        title: 'Error',
                        message: 'An error occurred while saving customer information.',
                        type: 'warning',
                    });
                }
            }

            this._disableWizard();
            this._saveCustomerInfo().then((result) => {
                if (result.success && result.partner_id) {
                    this.state.customer = result.partner_id;
                    return this._startOtp(result.partner_id).then((otpRes) => {
                        if (otpRes && otpRes.success) {
                            this.wizard.otpId = otpRes.otp_id;
                            this._showOtpModal({ expiresIn: otpRes.expires_in || 120 }, true);
                        } else if (otpRes && otpRes.is_otp_verified) {
                            this._markStepCompleted(this.wizard.currentStep);
                            this._onChangeStep(this.wizard.currentStep + 1);
                        } else {
                            this.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                        }
                    }).finally(() => {
                        this._enableWizard();
                    });
                } else if (result.success) {
                    this.displayNotification({ type: 'warning', title: 'Customer', message: 'Saved but verification could not start.' });
                } else {
                    this.displayNotification({
                        type: 'danger',
                        title: 'Error',
                        message: result.message || 'Customer Information could not be saved.',
                    });
                }
            }).catch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: 'Error',
                    message: `Connection error occurred. ${error.message || ''}`,
                });
            }).finally(() => {
                this._enableWizard();
            });
            return false;
        }
        return true;
    },

    _previousStep: function () {
        if (this.wizard.currentStep > 1) {
            this._onChangeStep(this.wizard.currentStep - 1);
        }
    },

    _initializeSellerInfoForm: function () {
        this._bindWizardToggle();
        this._prefillSellerFromAd();
    },

    _initializeProductInfoForm: function () {
        if (this.state.id > 0) {
            const self = this;
            this._getProductData().then(() => {
                const adData = self.values.ads[self.state.id];
                if (adData && adData.categ) {
                    self.ad.input.category.$.val(adData.categ);
                    self._onCategoryChange().then(() => {
                        self._prefillProductFromAd();
                    });
                }
            });
        } else {
            const categoryField = this.ad.input.category;
            if (!categoryField) {
                return;
            }

            const selectedValue = categoryField.$ && categoryField.$.length ? categoryField.$.val() : categoryField.value;
            if (selectedValue) {
                categoryField.value = selectedValue;
                this._onCategoryChange();
            } else {
                this._clearDynamicAttributes();
            }
        }
    },

    _initializeCustomerInfoForm: function () {
        this._bindRecipientToggle();
        this._prefillCustomerFromAd();
    },

    _initializePaymentForm: function () {
        if (this.state.different){
            this.payment.different.holder.$.prop('checked', true).trigger('change');
        }
        this._updatePaymentAmounts();
    },

    _getProductData: function() {
        const self = this;
        console.log('Loading product data for ad id:', self.state);
        return this._rpc({
            route: '/get/ad',
            params: { ad_id: self.state.id },
        }).then((product) => {
            if (product && product.success) {
                self.values.ads[product.ad.id] = {
                    attributes: product.ad.attributes || [],
                    categ: product.ad.categ_id?.id || product.ad.categ_id,
                    category_name: product.ad.categ_id?.name || '',
                    id: product.ad.id,
                    img: product.ad.image,
                    item_id: product.ad.item_id,
                    image: product.ad.image,
                    name: product.ad.name,
                    owner_id: product.ad.owner_id,
                    partner: product.ad.partner,
                    price: product.ad.price,
                    product_id: product.ad.id,
                    sale_state: product.ad.sale_state,
                    raw_state: product.ad.state,
                    iban: product.ad.iban,
                    vat: product.ad.vat,
                    owner_id: product.ad.owner_id,
                    customer_id: product.ad.customer_id,
                };
            }
        });
    },

    _markStepCompleted: function (stepNumber) {
        if (stepNumber >= 1 && stepNumber <= 4) {
            const $stepItem = $(`.steps__item:nth-child(${stepNumber})`);
            $stepItem.addClass('-completed');
        }
    },

    _bindUserTypeToggle: function (cfg) {
        const $root = typeof cfg.root === 'string' ? $(cfg.root) : cfg.root;
        if (!$root || !$root.length) return;

        const radioName = cfg.radioName || 'userType';
        const $radioInd = $root.find(`input[name="${radioName}"][value="individual"]`);
        const $radioCor = $root.find(`input[name="${radioName}"][value="corporate"]`);
        const $ind = cfg.individualSelector ? $root.find(cfg.individualSelector) : $();
        const $cor = cfg.corporateSelector ? $root.find(cfg.corporateSelector) : $();
        const $btnInd = cfg.buttonIndividual ? $root.find(cfg.buttonIndividual) : $();
        const $btnCor = cfg.buttonCorporate ? $root.find(cfg.buttonCorporate) : $();
        const $slider = cfg.sliderSelector ? $root.find(cfg.sliderSelector) : $();

        function setMode(mode) {
            const isInd = mode === 'individual';

            if ($ind.length) $ind.toggleClass('d-none', !isInd).toggle(isInd);
            if ($cor.length) $cor.toggleClass('d-none', isInd).toggle(!isInd);

            if ($radioInd.length) $radioInd.prop('checked', isInd);
            if ($radioCor.length) $radioCor.prop('checked', !isInd);

            if ($btnInd.length && $btnCor.length) {
                $btnInd
                    .toggleClass('btn-dark active', isInd)
                    .toggleClass('btn-outline-dark', !isInd);
                $btnCor
                    .toggleClass('btn-dark active', !isInd)
                    .toggleClass('btn-outline-dark', isInd);
            }

            if ($slider.length) {
                $slider.css('transform', isInd ? 'translateX(0%)' : 'translateX(100%)');
            }
        }

        $btnInd.off('click.userTypeToggle');
        $btnCor.off('click.userTypeToggle');
        $radioInd.off('change.userTypeToggle');
        $radioCor.off('change.userTypeToggle');

        if ($btnInd.length) {
            $btnInd.on('click.userTypeToggle', (e) => {
                e.preventDefault();
                setMode('individual');
            });
        }
        if ($btnCor.length) {
            $btnCor.on('click.userTypeToggle', (e) => {
                e.preventDefault();
                setMode('corporate');
            });
        }
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

        const selected = $root.find(`input[name="${radioName}"]:checked`).val() || 'individual';
        setMode(selected);
    },
    _bindWizardToggle: function () {
        this._bindUserTypeToggle({
            root: $('#sellerInfo'),
            radioName: 'userType',
            individualSelector: '.wizard-section-individual',
            corporateSelector: '.wizard-section-corporate',
            sliderSelector: '.radioTab__slider',
        });
    },

    _bindRecipientToggle: function() {
        this._bindUserTypeToggle({
            root: $('#customerInfo'),
            radioName: 'customerUserType',
            individualSelector: '#customerIndividual',
            corporateSelector: '#customerCorporate',
            sliderSelector: '.radioTab__slider',
        });
    },

    _saveSellerInfo: function () {
        const sellerType = $('input[name="userType"]:checked').val();
        let formData = {
            seller_type: sellerType,
        };
        const ad = this.state.id
        if (ad > 0) {
            formData = {...formData, ad_id: ad };
        }
        if (sellerType === 'corporate') {
            formData = {
                ...formData,
                seller_name: this.seller.input.corporate_title.$.val(),
                seller_email: this.seller.input.email_corporate.$.val(),
                seller_phone: this.seller.input.phone_corporate.$.val(),
                seller_tax_number: this.seller.input.tax_number.$.val(),
                seller_contact_person: this.seller.input.corporate_person.$.val(),
                seller_iban: this.seller.input.iban_corporate.$.val(),
                seller_iban_name: this.seller.input.iban_name_corporate.$.val(),
                seller_city: this.seller.input.city_corporate.$.val(),
            };
        } else {
            formData = {
                ...formData,
                seller_name: this.seller.input.name.$.val(),
                seller_email: this.seller.input.email_individual.$.val(),
                seller_phone: this.seller.input.phone_individual.$.val(),
                seller_tc_number: this.seller.input.tc.$.val(),
                seller_iban: this.seller.input.iban_individual.$.val(),
                seller_iban_name: this.seller.input.iban_name_individual.$.val(),
                seller_city: this.seller.input.city_individual.$.val(),
            };
        }
        return this._rpc({
            route: '/my/seller/save',
            params: formData,
        });
    },

    _startOtp: function(partnerId){
        this.currentOtpPartnerId = partnerId;
        return this._rpc({ route: '/my/otp/start', params: { partner_id: partnerId } });
    },

    _verifyOtp: function(code){
        return this._rpc({ route: '/my/otp/verify', params: { otp_id: this.wizard.otpId, code: code } });
    },

    _showOtpModal: function(expiresOrOpts, shouldAdvanceStep = false){
        const isObj = typeof expiresOrOpts === 'object' && expiresOrOpts !== null;
        const ttl = isObj ? (expiresOrOpts.expiresIn || expiresOrOpts.ttl || 120) : (typeof expiresOrOpts === 'number' ? expiresOrOpts : 120);
        this.shouldAdvanceStep = shouldAdvanceStep;

        const $modal = this._ensureOtpModal();
        const $timer = $modal.find('#otpTimer');
        const $inputs = $modal.find('.otp-inp');
        const $submitBtn = $modal.find('#otpSubmit');
        const $resendBtn = $modal.find('#otpResend');

        let seconds = ttl;

        $modal.css('display', 'flex');
        $timer.text(seconds);
        $submitBtn.prop('disabled', false).removeClass('disabled');
        $resendBtn.hide();
        $inputs.val('');
        $inputs.first().focus();

        if (this.otpTimer) {
            clearInterval(this.otpTimer);
        }

        this.otpTimer = setInterval(() => {
            seconds -= 1;
            if (seconds < 0) {
                seconds = 0;
            }
            $timer.text(seconds);
            if (seconds === 0) {
                clearInterval(this.otpTimer);
                $submitBtn.prop('disabled', true).addClass('disabled');
                $resendBtn.show();
            }
        }, 1000);
    },

    _ensureOtpModal: function() {
        if (!this.$otpModal || !this.$otpModal.length) {
            $('body').append(qweb.render('paylox.escrow.otp.modal'));
            this.$otpModal = $('#otpModal');
            this._bindOtpModalEvents();
        }
        return this.$otpModal;
    },

    _bindOtpModalEvents: function() {
        const self = this;
        const $modal = this.$otpModal;
        const $inputs = $modal.find('.otp-inp');

        $inputs.off('input.otp keydown.otp paste.otp');
        $inputs.on('input.otp', function(){
            this.value = this.value.replace(/\D/g,'').slice(0,1);
            if (this.value && this.nextElementSibling) {
                this.nextElementSibling.focus();
            }
            const code = $inputs.map((i, el) => el.value).get().join('');
            if (code.length === 4) {
                setTimeout(() => {
                    self._onClickOtpSubmit();
                }, 200);
            }
        });

        $inputs.on('keydown.otp', function(e){
            if (e.key === 'Backspace' && !this.value && this.previousElementSibling) {
                this.previousElementSibling.focus();
            }
        });

        $inputs.on('paste.otp', function(e){
            e.preventDefault();
            const pastedData = e.originalEvent.clipboardData.getData('text');
            const digits = pastedData.replace(/\D/g, '').slice(0, 4);
            digits.split('').forEach((digit, index) => {
                if ($inputs[index]) {
                    $inputs[index].value = digit;
                }
            });
            if (digits.length) {
                const targetIndex = Math.min(digits.length - 1, 3);
                $inputs[targetIndex].focus();
                if (digits.length === 4) {
                    self._onClickOtpSubmit();
                }
            }
        });

        $modal.off('click', '#otpCancel');
        $modal.on('click', '#otpCancel', function(e){
            e.preventDefault();
            self._closeOtpModal();
        });

        $modal.off('click', '#otpSubmit');
        $modal.on('click', '#otpSubmit', function(e){
            e.preventDefault();
            self._onClickOtpSubmit();
        });

        $modal.off('click', '#otpResend');
        $modal.on('click', '#otpResend', function(e){
            e.preventDefault();
            self._onClickOtpResend();
        });
    },

    _closeOtpModal: function() {
        if (this.otpTimer) {
            clearInterval(this.otpTimer);
            this.otpTimer = null;
        }
        if (this.$otpModal && this.$otpModal.length) {
            this.$otpModal.hide();
            this.$otpModal.find('.otp-inp').val('');
        }
    },

    _onClickOtpSubmit: function() {
        const $modal = this._ensureOtpModal();
        const $inputs = $modal.find('.otp-inp');
        const code = $inputs.map((i, el) => el.value).get().join('');

        if (code.length !== 4) {
            this.displayNotification({type:'warning', title:'OTP', message:'Lütfen 4 haneli kodu giriniz.'});
            return;
        }

        this._verifyOtp(code).then(res => {
            if (res && res.success) {
                this._closeOtpModal();
                this.displayNotification({
                    type: 'success',
                    title: 'OTP',
                    message: 'Phone number verified successfully'
                });
                if (this.shouldAdvanceStep) {
                    this._markStepCompleted(this.wizard.currentStep);
                    this._onChangeStep(this.wizard.currentStep + 1);
                }
            } else {
                this.displayNotification({ type:'danger', title:'OTP', message: (res && res.message) || 'Doğrulama başarısız' });
                $inputs.val('');
                $inputs.first().focus();
            }
        }).catch(() => {
            this.displayNotification({ type:'danger', title:'OTP', message:'Doğrulama sırasında hata oluştu' });
        });
    },

    _onClickOtpResend: function() {
        if (!this.currentOtpPartnerId) {
            this.displayNotification({ type:'warning', title:'OTP', message:'Partner information not found.' });
            return;
        }
        this._startOtp(this.currentOtpPartnerId).then(res => {
            if (res && res.success) {
                this.wizard.otpId = res.otp_id;
                this._showOtpModal(res.expires_in || 120, this.shouldAdvanceStep);
                this.displayNotification({ type:'success', title:'OTP', message:'Verification code has been resent.' });
            } else {
                this.displayNotification({ type:'danger', title:'OTP', message: (res && res.message) || 'OTP could not be resent.' });
            }
        }).catch(() => {
            this.displayNotification({ type:'danger', title:'OTP', message:'An unexpected error occurred while resending OTP.' });
        });
    },

    _saveCustomerInfo: function() {
        const self = this;
        const userType = $('input[name="customerUserType"]:checked').val();

        const data = {
            customer_type: userType,
            product_id: this.state.id,
        };

        if (userType === 'individual') {
            data.customer_name_surname = this.customer.input.name.$.val();
            data.customer_identity = this.customer.input.tc.$.val();
            data.customer_phone = this.customer.input.phone_individual.$.val();
            data.customer_email = this.customer.input.email_individual.$.val();
            data.customer_address = this.customer.input.address_individual.$.val();
        } else {
            data.customer_corporate_title = this.customer.input.corporate_title.$.val();
            data.customer_tax_number = this.customer.input.tax_number.$.val();
            data.customer_tax_office = this.customer.input.tax_office.$.val();
            data.customer_phone = this.customer.input.phone_corporate.$.val();
            data.customer_email = this.customer.input.email_corporate.$.val();
            data.customer_address = this.customer.input.address_corporate.$.val();
        }
        return this._rpc({
            route: '/my/customer/save',
            params: data,
        }).then((result) => {
            if (result.success && result.partner_id) {
                this._setState({ customer: result.partner_id });
            }
            return result;
        });
    },

    _showRemainingPaymentInfo: function() {
        const $remainingPaymentInfo = $('.remaining-payment-info[field="remaining.payment.info"]');
        if ($remainingPaymentInfo.length) {
            $remainingPaymentInfo.removeClass('d-none');
        }
    },

    _updatePaymentAmounts: async function() {
        let data = await rpc.query({
            route: '/payment/escrow/transaction-data',
            params: { product_id: this.state.id }
        });
        if (data && !data.error) {
            this.payment.amount.remaining.$.text(format.currency(data.remaining_amount, this.currency.position, this.currency.symbol, this.currency.decimal));
            if (data.different){
                this._setState({ different: true });
                const $card = $('.payment-info-card');
                $card.find('[field="payment.different.info.display.tc"]').text(data.different_holder.vat || '-');
                $card.find('[field="payment.different.info.display.name"]').text(data.different_holder.name || '-');
                $card.find('[field="payment.different.info.display.phone"]').text(data.different_holder.phone || '-');
                $card.find('[field="payment.different.info.display.email"]').text(data.different_holder.email || '-');

                this.payment.different.info.tc.value = data.different_holder.vat || '';
                this.payment.different.info.name.value = data.different_holder.name || '';
                this.payment.different.info.phone.value = data.different_holder.phone || '';
                this.payment.different.info.email.value = data.different_holder.email || '';

                if (data.different_holder.is_otp_verified){
                    const $icon = $card.find('[field="payment.different.info.display.phone"]').siblings('i');
                    $icon.removeClass('fa-exclamation-circle fa-spinner fa-spin').addClass('fa-check-circle');
                    this._isOtpValidate(this.payment.different.info.phone);
                }
            }
        }
        return data;
    },

    _onClickButtonPayment: function() {
        const params = {};
        if (this.card.number.value.length === 16) {
            if (this.state.different){
            params.vat = this.payment.different.info.tc.value;
            params.card_number = this.card.number.value;
            } else {
                params.vat = this.customer.input.tc.value;
                params.card_number = this.card.number.value;
            }

            this._rpc({
                route: '/payment/escrow/card/validate',
                params: {
                    ...params,
                },
            }).then((result) => {
                let message = (result && result.message) || 'Card validation failed';
                if (result && result.success) {
                    this._onFieldValid(this.card.number, true, 'Card is valid');
                    this.displayNotification({ 
                        type: 'success', 
                        title: 'Card Validation',
                        message: result.data
                    });
                } else {
                    this._onFieldValid(this.card.number, false, message);
                    this.displayNotification({ 
                        type: 'danger', 
                        title: 'Card Validation', 
                        message: (result && result.message) || 'Card validation failed' 
                    });
                }
            });

        }
    },

    _onToggleDifferentHolder: function(event) {
        this._setState({ different: event.target.checked });
        const isChecked = event.target.checked;
        const $assignmentSection = this.assignment.form.section.$;
        const $infoSection = this.payment.different.info.container.$;
        const $infoForm = this.payment.different.info.form.$;
        
        if (isChecked) {
            $assignmentSection.slideDown(300);
            $infoForm.slideDown(300);
        } else {
            $assignmentSection.slideUp(300);
            $infoForm.slideUp(300);
            $infoSection.slideUp(300);
        }
    },

    _onEditPaymentInfo: function(event) {
        const $card = $('.payment-info-card');
        const $form = $('.payment-info-edit');
        
        $card.slideUp(200, function() {
            $form.slideDown(300);
        });
    },

    _onCancelEditPaymentInfo: function(event) {
        const $card = $('.payment-info-card');
        const $form = $('.payment-info-edit');
        
        $form.slideUp(200, function() {
            $card.slideDown(300);
        });
    },

    _onSavePaymentInfo: function(event) {
        const tcValid = this.payment.different.info.tc.validate();
        const nameValid = this.payment.different.info.name.validate();
        const phoneValid = this.payment.different.info.phone.validate();
        const emailValid = this.payment.different.info.email.validate();
        
        if (tcValid && nameValid && phoneValid && emailValid) {
            this._updatePaymentInfoDisplay();
            
            const $card = $('.payment-info-card');
            const $form = $('.payment-info-edit');
            
            $form.slideUp(200, function() {
                $card.slideDown(300);
            });
        }
    },

    _updatePaymentInfoDisplay: function() {
        const params = {
            partner_id: this.state.customer,
            name: this.payment.different.info.name.value,
            vat: this.payment.different.info.tc.value,
            phone: this.payment.different.info.phone.value,
            email: this.payment.different.info.email.value,
        };
        
        this._rpc({
            route: '/payment/escrow/customer/card-holder/update',
            params: {
                ...params,
            },
        }).then((result) => {
            if (result && result.success) {
                this._setState({ customer: result.partner.id });
                return this._startOtp(result.partner.id).then((otpRes) => {
                    if (otpRes && otpRes.success) {
                        this.wizard.otpId = otpRes.otp_id;
                        this._showOtpModal(otpRes.expires_in || 120, false);
                    } else if (otpRes && otpRes.is_otp_verified) {
                        this.displayNotification({ 
                            type: 'success', 
                            title: 'OTP', 
                            message: 'Phone number is already verified' 
                        });
                    } else {
                        this.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                    }
                }).finally(() => {
                    this._enableWizard();
                const $card = $('.payment-info-card');
                    $card.find('[field="payment.different.info.display.tc"]').text(result.partner.vat || '-');
                    $card.find('[field="payment.different.info.display.name"]').text(result.partner.name || '-');
                    $card.find('[field="payment.different.info.display.phone"]').text(result.partner.phone || '-');
                    $card.find('[field="payment.different.info.display.email"]').text(result.partner.email || '-');
                });
            } else {
                this.displayNotification({
                    type: 'warning',
                    title: 'Error',
                    message: (result && result.error) || 'An error occurred while updating card holder information.',
                });
            }
        });

    },

    _clearCustomerInputs: function() {
        const $wiz = $('.escrow-wizard');
        $wiz.find('#customer_name_surname').value = null;
        $wiz.find('#customer_identity').value = null;
        $wiz.find('#customer_phone_individual').value = null;
        $wiz.find('#customer_email_individual').value = null;
        $wiz.find('#customer_address_individual').value = null;
        
        $wiz.find('#customer_corporate_title').value = null;
        $wiz.find('#customer_tax_number').value = null;
        $wiz.find('#customer_tax_office').value = null;
        $wiz.find('#customer_person').value = null;
        $wiz.find('#customer_phone_corporate').value = null;
        $wiz.find('#customer_email_corporate').value = null;
        $wiz.find('#customer_address_corporate').value = null;

        $wiz.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $wiz.find('.form__error-label, .just-validate-error-label').remove();
    },

    _onClickReturnToPayment: function(event) {
        event.preventDefault();
        const $remainingPaymentInfo = $('.remaining-payment-info[field="remaining.payment.info"]');
        $remainingPaymentInfo.addClass('d-none');
        const $paymentPanel = $('.payment-panel');
        $paymentPanel.removeClass('d-none').hide().slideDown(300);
        this._onChangeStep(4);
    },

    _onDownloadAssignmentForm: function(event) {
        event.preventDefault();
        const downloadUrl = '/escrow/assignment/form/download';
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = 'assignment_form.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },

    _onUploadAssignmentForm: function(event) {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        const $uploadStatus = this.assignment.form['upload.status'].$;

        const allowedTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
        if (!allowedTypes.includes(file.type)) {
            $uploadStatus.html('<div class="text-danger"><i class="fa fa-times"></i> Please upload only PDF, JPG, or PNG files.</div>');
            event.target.value = '';
            return;
        }

        const maxSize = 5 * 1024 * 1024;
        if (file.size > maxSize) {
            $uploadStatus.html('<div class="text-danger"><i class="fa fa-times"></i> File size must be less than 5MB.</div>');
            event.target.value = '';
            return;
        }

        $uploadStatus.html('<div class="text-info"><i class="fa fa-spinner fa-spin"></i> Uploading...</div>');

        const reader = new FileReader();
        reader.onload = () => {
            try {
                const dataUrl = reader.result || '';
                const base64 = String(dataUrl).split(',')[1] || '';
                this._rpc({
                    route: '/escrow/assignment/form/upload',
                    params: {
                        filename: file.name,
                        mimetype: file.type,
                        content: base64,
                    },
                }).then((result) => {
                    if (result && result.success) {
                        $uploadStatus.html('<div class="text-success"><i class="fa fa-check"></i> File uploaded successfully</div>');
                        const $downloadBtn = this.assignment.form.download.$;
                        $downloadBtn.removeClass('d-none');
                    } else {
                        $uploadStatus.html('<div class="text-danger"><i class="fa fa-times"></i> ' + ((result && result.error) || 'Upload failed') + '</div>');
                        event.target.value = '';
                    }
                }).catch(() => {
                    $uploadStatus.html('<div class="text-danger"><i class="fa fa-times"></i> Upload failed. Please try again.</div>');
                    event.target.value = '';
                });
            } catch (e) {
                $uploadStatus.html('<div class="text-danger"><i class="fa fa-times"></i> Could not read the file.</div>');
                event.target.value = '';
            }
        };
        reader.onerror = () => {
            $uploadStatus.html('<div class="text-danger"><i class="fa fa-times"></i> Could not read the file.</div>');
            event.target.value = '';
        };
        reader.readAsDataURL(file);
    },

    _lookupPartnerByIdentity: function(partnerType, userType, identityValue, identityLength) {
        if (!identityValue || identityValue.length !== identityLength) {
            return;
        }
        if (identityLength === 11 && !this._isTcknValid(identityValue)) {
            return;
        }
        if (identityLength === 10 && !this._isVatValid(identityValue)) {
            return;
        }

        const route = '/my/partner/lookup'
        const typeParam = partnerType === 'seller' ? 'seller_type' : 'customer_type';
        const dataKey = 'data'
        const lookupType = partnerType === 'seller' ? 'owner' : 'customer';

        this._rpc({
            route: route,
            params: {
                identity: identityValue,
                type: lookupType,
                [typeParam]: userType,
            }
        }).then((result) => {
            if (result && result.success && result.found) {
                const data = result[dataKey];
                this._fillPartnerData(partnerType, userType, data);
            }
        }).catch((error) => {
            console.error(`Error looking up ${partnerType}:`, error);
        });
    },

    _fillPartnerData: function(partnerType, userType, data) {
        const inputs = partnerType === 'seller' ? this.seller.input : this.customer.input;
        
        if (userType === 'corporate') {
            if (partnerType === 'seller') {
                this._bindWizardToggle();
                inputs.corporate_title.value = data.name || '';
                inputs.tax_number.$.val(data.vat || '');
                if (inputs.tax_office) inputs.tax_office.value = data.commercial_partner_id?.name || ''
                if (inputs.wizard_address) inputs.wizard_address.value = this._formatAddress(data);
                inputs.corporate_person.value = data.name || '';
                inputs.phone_corporate.value = data.phone || '';
                inputs.email_corporate.value = data.email || '';
                if (inputs.address_corporate) inputs.address_corporate.value = this._formatAddress(data);
                if (inputs.city_corporate && data.city) inputs.city_corporate.$.val(data.city);
                this._isOtpValidate(inputs.phone_corporate);
                
                if (data.bank_ids && data.bank_ids.length > 0) {
                    const bankAccount = data.bank_ids[0];
                    inputs.iban_corporate.value = this._formatIbanDisplay(bankAccount.acc_number);
                    inputs.iban_name_corporate.value = bankAccount.acc_holder_name || data.name;
                    this._isIbanVerified(inputs.iban_corporate, inputs.tax_number);
                }
            } else {
                inputs.corporate_title.value = data.name || '';
                inputs.tax_number.value = data.vat || '';
                if (inputs.tax_office) inputs.tax_office.value = data.tax_office || '';
                inputs.phone_corporate.value = data.phone || '';
                inputs.email_corporate.value = data.email || '';
                if (inputs.address_corporate) inputs.address_corporate.value = data.address || '';
                this._isOtpValidate(inputs.phone_corporate);
            }
        } else {
            if (partnerType === 'seller') {
                this._bindWizardToggle();
                inputs.name.value = data.name || '';
                inputs.tc.value = data.vat || '';
                inputs.phone_individual.value = data.phone || '';
                inputs.email_individual.value = data.email || '';
                if (inputs.city_individual && data.city) inputs.city_individual.$.val(data.city);
                this._isOtpValidate(inputs.phone_individual);
                
                if (data.bank_ids && data.bank_ids.length > 0) {
                    const bankAccount = data.bank_ids[0];
                    inputs.iban_individual.value = this._formatIbanDisplay(bankAccount.acc_number);
                    inputs.iban_name_individual.value = bankAccount.acc_holder_name || data.name;
                    this._isIbanVerified(inputs.iban_individual, inputs.tc);
                }
            } else {
                inputs.name.value = data.name || '';
                inputs.phone_individual.value = data.phone || '';
                inputs.email_individual.value = data.email || '';
                if (inputs.address_individual) inputs.address_individual.value = data.address || '';
                inputs.tc.value = data.vat || '';
                this._isOtpValidate(inputs.phone_individual);
            }
        }
    },

    _initializeFileUploads: function(transactions) {
        const self = this;
        
        transactions.forEach(function(payment) {
            const fileInputId = `fileConveyance_${payment.id}`;
            const uploadedFilesId = `uploadedFiles_${payment.id}`;
            const $fileInput = $(`#${fileInputId}`);
            const $uploadedContainer = $(`#${uploadedFilesId}`);
            const $uploadedList = $uploadedContainer.find('.uploaded-files-list');

            if (payment.conveyance_attachment) {
                const fileName = payment.conveyance_file_name || 'Conveyance Form';
                const uploadDate = payment.conveyance_upload_date ? 
                    new Date(payment.conveyance_upload_date).toLocaleDateString() : '';
                
                let statusIcon = 'fa-check text-success';
                let statusText = 'Uploaded';
                
                statusIcon = 'fa-paper-plane text-info';
                statusText = 'Sent';
                $uploadedList.html(`
                    <div class="uploaded-file-item d-flex align-items-center p-2 border rounded">
                        <i class="fa fa-file-o mr-2"></i>
                        <div class="file-info flex-grow-1">
                            <div class="file-name font-weight-bold">${fileName}</div>
                            <div class="file-details text-muted small">
                                <span><i class="fa ${statusIcon.split(' ')[0]} mr-1"></i>${statusText}</span>
                                ${uploadDate ? `<span class="ml-2">• ${uploadDate}</span>` : ''}
                            </div>
                        </div>
                        <div class="file-actions">
                            <a href="${payment.receipt_url}" 
                               target="_blank" 
                               class="btn btn-sm btn-outline-primary mr-2"
                               title="Download File">
                                <i class="fa fa-download"></i>
                            </a>
                        </div>
                    </div>
                `);
                $uploadedContainer.show();
            }
        
            if ($fileInput.length) {
                const pond = FilePond.create($fileInput[0], {
                    allowMultiple: false,
                    credits: false,
                    acceptedFileTypes: ['image/png', 'image/jpeg', 'image/gif', 'application/pdf'],
                    maxFileSize: '10MB',
                    labelIdle: `<svg class="w-100" width="42" height="42" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M31.4998 33.2514C30.5318 33.2514 29.7484 32.468 29.7484 31.5C29.7484 30.532 30.5318 29.7486 31.4998 29.7486C35.3594 29.7486 38.5012 26.6068 38.5012 22.7473C38.5012 19.0723 35.626 16.0084 31.9592 15.7705L30.9256 15.709L30.4867 14.7779C28.7559 11.1152 25.0316 8.74863 20.9998 8.74863C16.968 8.74863 13.2438 11.1152 11.5129 14.7779L11.074 15.709L10.0445 15.7746C6.37363 16.0125 3.50254 19.0764 3.50254 22.7514C3.50254 26.6109 6.64434 29.7527 10.5039 29.7527C11.4719 29.7527 12.2553 30.5361 12.2553 31.5041C12.2553 32.4721 11.4719 33.2555 10.5039 33.2555C4.7125 33.2555 0.00390625 28.5469 0.00390625 22.7555C0.00390625 17.5834 3.79785 13.2193 8.80996 12.4031C11.2709 8.02676 15.9508 5.25 20.9998 5.25C26.0488 5.25 30.7287 8.02676 33.1938 12.3949C38.2059 13.2111 41.9998 17.5793 41.9998 22.7514C41.9998 28.5387 37.2912 33.2514 31.4998 33.2514Z" fill="black"/>
                            <path d="M26.2502 32.3737C25.8032 32.3737 25.3561 32.2014 25.0116 31.861L21.0002 27.8497L16.9889 31.861C16.3081 32.5459 15.1965 32.5459 14.5157 31.861C13.8307 31.176 13.8307 30.0686 14.5157 29.3877L19.7657 24.1377C20.4465 23.4528 21.5581 23.4528 22.2389 24.1377L27.4889 29.3877C28.1739 30.0727 28.1739 31.1801 27.4889 31.861C27.1444 32.2055 26.6973 32.3737 26.2502 32.3737Z" fill="#2414D8"/>
                            <path d="M21.0004 39.375C20.0324 39.375 19.249 38.5916 19.249 37.6236V25.3764C19.249 24.4084 20.0324 23.625 21.0004 23.625C21.9684 23.625 22.7518 24.4084 22.7518 25.3764V37.6277C22.7518 38.5916 21.9684 39.375 21.0004 39.375Z" fill="#2414D8"/>
                        </svg>
                        <span class="text-600">Select Image or Take New</span>
                        <div class="text-600">No Image Selected</div>`,
                    server: {
                        process: function (fieldName, file, metadata, load, error, progress, abort, transfer, options) {
                            const reader = new FileReader();
                            reader.onload = function(e) {
                                const base64Data = e.target.result.split(',')[1];
                                self._rpc({
                                    route: '/payment/escrow/upload-conveyance',
                                    params: {
                                        file_name: file.name,
                                        file_data: base64Data,
                                        file_type: file.type,
                                        payment_id: payment.id
                                    }
                                }).then(function(result) {
                                    if (result && result.success) {
                                        load(result.attachment_id);
                                        const fileName = file.name;
                                        const fileSize = (file.size / 1024 / 1024).toFixed(2) + ' MB';
                                        
                                        $uploadedList.html(`
                                            <div class="uploaded-file-item d-flex align-items-center p-2 border rounded">
                                                <i class="fa fa-file-o mr-2"></i>
                                                <div class="file-info flex-grow-1">
                                                    <div class="file-name font-weight-bold">${fileName}</div>
                                                    <div class="file-size text-muted small">${fileSize}</div>
                                                </div>
                                                <i class="fa fa-check text-success"></i>
                                            </div>
                                        `);
                                        $uploadedContainer.show();
                                    } else {
                                        error(result && result.error || 'Upload failed');
                                    }
                                }).catch(function(err) {
                                    console.error('Upload error:', err);
                                    error('Upload failed');
                                });
                            };
                            
                            reader.onerror = function() {
                                error('Could not read file');
                            };
                            reader.readAsDataURL(file);
                            return {
                                abort: () => {
                                    abort();
                                }
                            };
        }
                    }
                });
                if (payment.conveyance_attachment) {
                    const byteCharacters = atob(payment.conveyance_attachment.data);
                    const byteNumbers = new Array(byteCharacters.length);
                    for (let i = 0; i < byteCharacters.length; i++) {
                        byteNumbers[i] = byteCharacters.charCodeAt(i);
                    }
                    const byteArray = new Uint8Array(byteNumbers);
                    const blob = new Blob([byteArray], { type: payment.conveyance_attachment.mimetype });
                    const file = new File([blob], payment.conveyance_file_name || 'Conveyance Form', { type: payment.conveyance_attachment.mimetype });
                    pond.addFile(file, {type: 'local'});
        }
                $fileInput.data('pond', pond);
            }
        });
    },

    _bindFilterEvents: function() {
        this.$('[field="ad.search"]').on('input', this._onSearchInput.bind(this));
        this.$('[field="ad.category.filter"] button').on('click', this._onCategoryFilterClick.bind(this));
        this.$('#price-min, #price-max').on('input', this._onPriceInput.bind(this));
        this.$('#price-range').on('input', this._onPriceRangeInput.bind(this));
        this.$('[field="ad.state.filter"] button').on('click', this._onStateFilterClick.bind(this));
    },

    _onSearchInput: function(e) {
        this.filterState.search = $(e.currentTarget).val().toLowerCase();
        this._applyFilters();
    },

    _onCategoryFilterClick: function(e) {
        const $btn = $(e.currentTarget);
        this.filterState.category = $btn.data('category');
        this.$('[field="ad.category.filter"] button').removeClass('active');
        $btn.addClass('active');
        this._applyFilters();
    },

    _onPriceInput: function(e) {
        const min = parseFloat(this.$('#price-min').val());
        const max = parseFloat(this.$('#price-max').val());
        this.filterState.priceMin = isNaN(min) ? null : min;
        this.filterState.priceMax = isNaN(max) ? null : max;
        this._applyFilters();
    },

    _onPriceRangeInput: function(e) {
        const val = $(e.currentTarget).val();
        this.$('#price-max').val(val);
        this.filterState.priceMax = parseFloat(val);
        this._applyFilters();
    },

    _applyFilters: function() {
        const { search, category, state, priceMin, priceMax } = this.filterState;
        
        this.state.pagination.filteredAds = [];
        
        const isListView = this.$('.escrow-ad-list').is(':visible');
        const isGridView = this.$('.escrow-ad-grid').is(':visible');
        
        let adRows;
        if (isListView) {
            adRows = this.$('.escrow-ad-list .escrow-ad-list-item');
        } else if (isGridView) {
            adRows = this.$('.escrow-ad-grid .escrow-ad-grid-item');
        } else {
            adRows = this.$('.escrow-ad-list .escrow-ad-list-item');
        }
        
        adRows.each((i, element) => {
            const $element = $(element);
            const id = $element.data('id');
            const data = this.values.ads[id];
            
            if (!data) return;
            
            let matches = true;
            
            if (search && !data.name.toLowerCase().includes(search)) {
                matches = false;
            }
            
            if (matches && category !== 'all') {
                const categId = (typeof data.categ === 'object' && data.categ !== null) ? data.categ.id : data.categ;
                if (String(categId) !== String(category)) {
                    matches = false;
                }
            }
            
            if (matches && state !== 'all') {
                if (state === 'cancelled') {
                    if (data.raw_state !== 'cancelled') matches = false;
                } else if (state === 'sold') {
                    if (data.raw_state !== 'sold') matches = false;
                } else {
                    if (data.raw_state === 'cancelled' || data.raw_state === 'sold') {
                        matches = false;
                    } else {
                        const currentAdState = data.state || 'waiting';
                        if (currentAdState !== state) {
                            matches = false;
                        }
                    }
                }
            }
            
            if (matches) {
                const price = parseFloat(data.price) || 0;
                if (priceMin !== null && price < priceMin) matches = false;
                if (priceMax !== null && price > priceMax) matches = false;
            }
            
            if (matches) {
                this.state.pagination.filteredAds.push(element);
            }
        });
        
        this.state.pagination.currentPage = 1;
        this._updatePagination();
    },

    _onStateFilterClick: function(e) {
        const clickedButton = $(e.currentTarget);
        const state = clickedButton.data('state');
        
        this.filterState.state = state;
        this._setState({ filterState: state });
        
        const filterContainer = this.$('[field="ad.state.filter"]');
        if (filterContainer.length) {
            filterContainer.find('.btn').each(function() {
                const $btn = $(this);
                $btn.removeClass('active btn-primary btn-success btn-warning btn-info btn-secondary text-white')
                    .addClass('btn-light');
                $btn.find('i').removeClass('text-white');
            });
            
            clickedButton.removeClass('btn-light').addClass('active text-white');
            clickedButton.find('i').addClass('text-white');
            
            if (state === 'new') clickedButton.addClass('btn-success');
            else if (state === 'waiting') clickedButton.addClass('btn-warning');
            else if (state === 'draft') clickedButton.addClass('btn-secondary');
            else if (state === 'waiting_payment') clickedButton.addClass('btn-info');
            else if (state === 'waiting_official_doc') clickedButton.addClass('btn-info');
            else if (state === 'waiting_transfer') clickedButton.addClass('btn-primary');
            else if (state === 'transferred') clickedButton.addClass('btn-success');
            else if (state === 'sold') clickedButton.addClass('btn-dark');
            else if (state === 'cancelled') clickedButton.addClass('btn-danger');
            else clickedButton.addClass('btn-secondary');
        }

        this._applyFilters();
    },
    
    _onSortChange: function(e) {
        const sortValue = $(e.currentTarget).val();
        this._sortAds(sortValue);
    },
    
    _sortAds: function(sortType) {
        const listContainer = this.$('.escrow-ad-list .ad-list-container');
        const gridContainer = this.$('.escrow-ad-grid .escrow-ad-grid-container');
        
        const listItems = listContainer.find('.escrow-ad-list-item').get();
        listItems.sort((a, b) => this._compareAds(a, b, sortType));
        listContainer.empty().append(listItems);
        
        const gridItems = gridContainer.find('.escrow-ad-grid-item').get();
        gridItems.sort((a, b) => this._compareAds(a, b, sortType));
        gridContainer.empty().append(gridItems);
        
        this._updatePagination();
    },
    
    _compareAds: function(a, b, sortType) {
        const aEl = $(a);
        const bEl = $(b);
        const aId = aEl.data('id');
        const bId = bEl.data('id');
        const aData = this.values.ads[aId] || {};
        const bData = this.values.ads[bId] || {};
        
        switch(sortType) {
            case 'date_desc':
                return new Date(bData.create_date || 0) - new Date(aData.create_date || 0);
            case 'date_asc': 
                return new Date(aData.create_date || 0) - new Date(bData.create_date || 0);
            case 'price_desc':
                return (bData.amount || 0) - (aData.amount || 0);
            case 'price_asc':
                return (aData.amount || 0) - (bData.amount || 0);
            case 'name_desc':
                return (bData.name || '').localeCompare(aData.name || '');
            case 'name_asc':
                return (aData.name || '').localeCompare(bData.name || '');
            default:
                return 0;
        }
    },

    _onPaginationPrev: function(e) {
        e.preventDefault();
        if (this.state.pagination.currentPage > 1) {
            this.state.pagination.currentPage--;
            this._updatePagination();
        }
    },

    _onPaginationNext: function(e) {
        e.preventDefault();
        if (this.state.pagination.currentPage < this.state.pagination.totalPages) {
            this.state.pagination.currentPage++;
            this._updatePagination();
        }
    },

    _onPaginationSizeChange: function(e) {
        this.state.pagination.pageSize = parseInt($(e.currentTarget).val());
        this.state.pagination.currentPage = 1;
        this._updatePagination();
    },

    _updatePagination: function() {
        const isListView = this.$('.escrow-ad-list').is(':visible');
        const isGridView = this.$('.escrow-ad-grid').is(':visible');
        
        let allAds;
        if (isListView) {
            allAds = this.$('.escrow-ad-list .escrow-ad-list-item');
        } else if (isGridView) {
            allAds = this.$('.escrow-ad-grid .escrow-ad-grid-item');
        } else {
            allAds = this.$('.escrow-ad-list .escrow-ad-list-item');
        }
        
        const filteredAds = this.state.pagination.filteredAds || [];

        this.state.pagination.totalItems = filteredAds.length;
        this.state.pagination.totalPages = Math.ceil(this.state.pagination.totalItems / this.state.pagination.pageSize);

        const startIndex = (this.state.pagination.currentPage - 1) * this.state.pagination.pageSize;
        const endIndex = startIndex + this.state.pagination.pageSize;

        allAds.hide();
        const itemsToShow = filteredAds.slice(startIndex, endIndex);
        $(itemsToShow).show();

        this._updatePaginationUI();
    },

    _updatePaginationUI: function() {
        if (!this.ad || !this.ad.pagination) {
            return;
        }

        if (this.ad.pagination.current && this.ad.pagination.current.$) {
            this.ad.pagination.current.$.text(this.state.pagination.currentPage);
        }

        const startItem = (this.state.pagination.currentPage - 1) * this.state.pagination.pageSize + 1;
        const endItem = Math.min(this.state.pagination.currentPage * this.state.pagination.pageSize, this.state.pagination.totalItems);
        
        if (this.ad.pagination.showing && this.ad.pagination.showing.$) {
            this.ad.pagination.showing.$.text(`${startItem}-${endItem}`);
        }
        
        if (this.ad.pagination.total && this.ad.pagination.total.$) {
            this.ad.pagination.total.$.text(this.state.pagination.totalItems);
        }

        if (this.ad.pagination.prev && this.ad.pagination.prev.$) {
            this.ad.pagination.prev.$.toggleClass('disabled', this.state.pagination.currentPage <= 1);
        }
        
        if (this.ad.pagination.next && this.ad.pagination.next.$) {
            this.ad.pagination.next.$.toggleClass('disabled', this.state.pagination.currentPage >= this.state.pagination.totalPages);
        }

        if (this.ad.pagination.container && this.ad.pagination.container.$) {
            this.ad.pagination.container.$.toggle(this.state.pagination.totalItems > 0);
        }
    },

    _onInsuranceSubmit: function(e) {
        e.preventDefault();
        
        const isValid = [
            this.insurance.input.birth_date.validate(),
            this.insurance.input.vat.validate(),
            this.insurance.input.gsmNo.validate(),
            this.insurance.input.email.validate(),
            this.insurance.input.plate.validate(),
            this.insurance.input.license_no.validate(),
            this.insurance.input.year.validate(),
            this.insurance.input.brand.validate(),
            this.insurance.input.model.validate(),
            // this.insurance.input.chassis_no.validate(),
            // this.insurance.input.engine_no.validate(),
            // this.insurance.input.registration_date.validate(),
            // this.insurance.input.model.validate(),
            // this.insurance.input.year.validate(),
        ].every(Boolean);

        if (!isValid) {
            return;
        }

        const extractName = (label = '') => {
            if (!label) return '';
            const parts = label.split(' - ');
            if (parts.length > 1) {
                return parts.slice(1).join(' - ').trim();
            }
            return label.trim();
        };

        const data = {
            birth_date: this.insurance.input.birth_date.value,
            vat: this.insurance.input.vat.value,
            gsmNo: this.insurance.input.gsmNo.value,
            email: this.insurance.input.email.value,
            plate: this.insurance.input.plate.value,
            license_no: this.insurance.input.license_no.value,
            year: this.insurance.input.year.value,
            brand_code: this.insurance.input.brand.value,
            brand_name: extractName(this.insurance.input.brand.text || ''),
            model_code: this.insurance.input.model.value,
            model_name: extractName(this.insurance.input.model.text || ''),
            // chassis_no: this.insurance.input.chassis_no.value,
            // engine_no: this.insurance.input.engine_no.value,
            // registration_date: this.insurance.input.registration_date.value,
            // model: this.insurance.input.model.text || this.insurance.input.model.value,
        };

        this.insurance.button.submit.$.prop('disabled', true);
        const infoTitle = _t('Insurance Quote');
        const preparingMessage = _t('Your insurance quote is being prepared...');

        this.displayNotification({
            type: 'info',
            title: infoTitle,
            message: preparingMessage,
        });

        setTimeout(() => {
            $('#insuranceQuoteModal').modal('hide');
        }, 300);

        rpc.query({
            route: '/escrow/insurance/quote',
            params: data
        }).then((result = {}) => {
            const defaultError = _t('An error occurred. Please try again.');
            if (result.success) {
                const quotes = Array.isArray(result.quotes) ? result.quotes : [];
                if (quotes.length > 0) {
                    this._resetInsuranceForm();
                    quotes.forEach((quote) => {
                        const toastType = quote.success ? 'success' : 'warning';
                        const toastTitle = quote.success ? infoTitle : _t('Insurance Quote Error');
                        const infoParts = [];
                        if (quote.reference) {
                            infoParts.push(`${_t('Reference')}: ${quote.reference}`);
                        }
                        if (quote.amount) {
                            infoParts.push(`${_t('Amount')}: ${quote.amount}`);
                        }
                        if (quote.details) {
                            infoParts.push(quote.details);
                        }
                        const toastMessage = infoParts.filter(Boolean).join(' • ') || (quote.success ? _t('The quote was successfully created.') : _t('The quote could not be created.'));

                        this.displayNotification({
                            type: toastType,
                            title: toastTitle,
                            message: toastMessage,
                        });
                    });
            } else {
                    const noQuoteMessage = result.message || _t('No insurance offer was returned. Please verify vehicle information and try again.');
                    this.displayNotification({
                        type: 'warning',
                        title: infoTitle,
                        message: noQuoteMessage,
                    });
                }
            } else {
                const errorMessage = result.message || defaultError;
                this.displayNotification({
                    type: 'danger',
                    title: infoTitle,
                    message: errorMessage,
                });
            }
        }).catch((error) => {
            const errorMessage = _t('An error occurred. Please try again.');
            this.displayNotification({
                type: 'danger',
                title: infoTitle,
                message: errorMessage,
            });
            console.error('Insurance quote error:', error);
        }).finally(() => {
            this.insurance.button.submit.$.prop('disabled', false);
        });
    },
});
