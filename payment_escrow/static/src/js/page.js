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
                this.payment.amount.paid.$.text(this._formatCurrency(value));
                return valid;
            }
        })
        this.partner = new fields.integer({
            default: 0,
        });
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
                tc: new fields.float({
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
                    events: [['input', () => this._isIbanVerified(this.seller.input.iban_individual)]],
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
                tax_number: new fields.string({
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
                    events: [['input', () => this._isIbanVerified(this.seller.input.iban_corporate)]],
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
                    validate: async () => {
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

        this.ad = {
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
                brand: new fields.selection({
                    validate: () => {
                        const field = this.ad.input.brand;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Brand is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                year: new fields.string({
                    validate: () => {
                        const field = this.ad.input.year;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Year is required');
                            valid = false;
                        } else {
                            let date = new Date();
                            let year = date.getFullYear();
                            if (field.value > year) {
                                message = _.str.sprintf(_t('Year cannot be later than %s.'), year);
                                valid = false;
                            }
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                vin: new fields.string({
                    mask: /^[A-Z0-9]{0,17}$/,
                    prepareChar: str => str.toUpperCase(),
                    events: [
                        ['input', function() {
                            const field = this.ad.input.vin;
                            if (field.value && field.value.length === 17) {
                                this._onVinComplete(field.value);
                            }
                        }]
                    ],
                    validate: () => {
                        const field = this.ad.input.vin;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('VIN is required');
                            valid = false;
                        } else if (field.value.length !== 17) {
                            message = _t('VIN must be exactly 17 characters');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                plate: new fields.string({
                    validate: () => {
                        const field = this.ad.input.plate;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Plate is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                fileLicence: new fields.file({
                    name: 'fileLicence',
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
                        const field = this.ad.input.fileLicence;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Licence image is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
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

        this.payment = {
            different: {
                holder: new fields.boolean({
                    events: [['change', this._onToggleDifferentHolder]]
                }),
                info: {
                    container: new fields.element(),
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
        //let hash = window.location.hash.split('#')[1];
        let hash = new URLSearchParams(window.location.search).get('');
        if (hash) {
            try {
                let state = JSON.parse(atob(hash));
                Object.assign(this.state, {
                    id: state.i,
                    step: state.s,
                });
            } catch {
                window.history.replaceState(null, '', window.location.pathname);
            }
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
            this._startToggles();
            $('.escrow-ad-wrapper').removeClass('d-none');
            framework.hideLoading();
        });
    },

    _onFieldValid: function(field, valid, message='') {
        field.$.closest('.form__group').find('.form__error-label, .just-validate-error-label').remove();
        if (valid) {
            field.$.removeClass('is-invalid -error just-validate-error-field').addClass('is-valid');
        } else {
            field.$.addClass('is-invalid -error just-validate-error-field').removeClass('is-valid');
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
                    if (result.data.model_year) {
                        self.ad.input.year.value = result.data.model_year
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
        const value = field.value;
        if (value.length === 10) {
            //this._showFieldLoadingIcon(field);
            let result = await this._rpc({
                route: '/my/otp/validate',
                params: { otp: value },
            });
            if (result) {
                this._showFieldSuccessIcon(field);
                return result;
            }
        } 
        this._hideFieldIcon(field);
    },

    _isIbanVerified: async function(field) {
        let iban = field._.masked.value;
        if (this._isIbanValid(iban)) {
            //this._showFieldLoadingIcon(field);
            let result = await this._rpc({
                route: '/my/iban/verify',
                params: { iban },
            });
            if (result) {
                this._showFieldSuccessIcon(field);
                return result;
            }
        }
        this._hideFieldIcon(field);
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

    _formatPhoneNumber: function(field){
        if (field.value.length <= 3) {
        } else if (field.value.length <= 6) {
            field.value = field.value.substring(0, 3) + ' ' + field.value.substring(3);
        } else {
            field.value = field.value.substring(0, 3) + ' ' + 
                            field.value.substring(3, 6) + ' ' + 
                            field.value.substring(6);
        }
    },

    _formatEmail: function(value) {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailPattern.test(value);
    },

    _onToggleVehicleHolder: function() {
        const id = this.state.id;
        if (this.values.ads[id].state === 'sold') {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('This ad has already been finalized.'),
            });
        } else {
            this.state.item_id = this.values.ads[id].item_id;
            if (id) {
                this._openSellerEditForCard(id, 'vehicle');
            }
        }
    },

    _onToggleSellerHolder: function() {
        const id = this.state.id;
        if (this.values.ads[id].state === 'sold') {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('This ad has already been finalized.'),
            });
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
        $('[field="ad.item"][data-value]').each((i, e) => {
            const $this = $(e);
            const values = $this.data('value');
            this.values.ads[e.dataset.id] = {
                img: $this.find('.escrow-ad-item-image img').attr('src'),
                name: $this.find('.escrow-ad-item-name').text().trim(),
                price: $this.find('.escrow-ad-item-price').data('value'),
                state: $this.find('.escrow-ad-item-state').data('value'),
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
                this.ad.view.list.$.stop(true, true).fadeIn(400);
            } else {
                this.ad.view.list.$.stop(true, true).hide();
                this.ad.view.grid.$.stop(true, true).fadeIn(400);
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
        this.state.id = 0;
        this._onChangeStep(1);
    },

    _closeSidebar: function() {
        $('.escrow-ad-wrapper').removeClass('blur');
        $('.escrow-ad-sidebar-section').addClass('d-none');
        this.ad.sideback.$.addClass('d-none');
        this.ad.sidebar.$.removeClass('show');
    },

    _prefillSellerFromAd: function(adData) {
        const $wiz = $('.escrow-wizard');
        
        if (adData.owner_id) {
            this._rpc({
                route: '/my/partner/get',
                params: { partner_id: adData.owner_id }
            }).then((ownerData) => {
                if (ownerData.success) {
                    const owner = ownerData.partner;
                    if (owner.is_company) {
                        $wiz.find('input[name="userType"][value="corporate"]').prop('checked', true);
                        this._bindWizardToggle();
                        this.seller.input.corporate_title.$.val(owner.name || '');
                        this.seller.input.tax_number.$.val(owner.vat || '');
                        this.seller.input.tax_office.$.val(owner.commercial_partner_id?.name || '');
                        this.seller.input.wizard_address.$.val(this._formatAddress(owner));
                        this.seller.input.corporate_person.$.val(owner.name || '');
                        this.seller.input.phone_corporate.$.val(owner.phone || '');
                        this.seller.input.email_corporate.$.val(owner.email || '');
                        this.seller.input.address_corporate.$.val(this._formatAddress(owner));
                        this._isOtpValidate(this.seller.input.phone_corporate);
                        if (owner.bank_ids && owner.bank_ids.length > 0) {
                            const bankAccount = owner.bank_ids[0];
                            this.seller.input.iban_corporate.value = this._formatIbanDisplay(bankAccount.acc_number);
                            this.seller.input.iban_name_corporate.value = bankAccount.api_merchant || owner.name;
                            this._isIbanVerified(this.seller.input.iban_corporate);
                        }
                    } else {
                        $wiz.find('input[name="userType"][value="individual"]').prop('checked', true);
                        this._bindWizardToggle();
                        this.seller.input.name.value = owner.name || '';
                        this.seller.input.tc.value = owner.vat || '';
                        this.seller.input.phone_individual.value = owner.phone || '';
                        this.seller.input.email_individual.value = owner.email || '';
                        this._isOtpValidate(this.seller.input.phone_individual);
                        if (owner.bank_ids && owner.bank_ids.length > 0) {
                            const bankAccount = owner.bank_ids[0];
                            this.seller.input.iban_individual.value = this._formatIbanDisplay(bankAccount.acc_number);
                            this.seller.input.iban_name_individual.value = bankAccount.api_merchant || owner.name;
                            this._isIbanVerified(this.seller.input.iban_individual);
                        }
                    }
                }
                return Promise.resolve();
            }).catch(() => {
                console.warn('Could not load owner data for prefill');
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
                    $item.find('.seller-iban').text(self.values.ads[adId].seller_iban);
                }
            }
        }).catch(() => {
            console.warn('Could not load seller data for sidebar');
        });
        $wiz.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $wiz.find('.form__error-label, .just-validate-error-label').remove();
    },

    _prefillProductFromAd: function(adData) {
        if (!adData) return;

        if (adData.price) {
            this.ad.input.price.value = format.float(adData.price);
        }
        if (adData.categ) {
            this.ad.input.category.$.val(adData.categ);
            this.ad.input.category.$.trigger('change');
        }
        
        if (adData.vin) {
            this.ad.input.vin.value = adData.vin;
        }
        if (adData.plate) {
            this.ad.input.plate.value = adData.plate;
        }
        
        if (adData.brand_id) {
            this.ad.input.brand.$.val(adData.brand_id);
            this.ad.input.brand.$.trigger('change');
        }
        if (adData.year) {
            this.ad.input.year.value = adData.year;
        }

        if (adData.img) {
            this.ad.input.fileLicence.value = adData.img;
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

    _saveAdData: function() {
        const isEditMode = this.state.id > 0;
        let params;
        params = {
            id: isEditMode ? this.state.id : null,
            categ_id: parseInt(this.ad.input.category.$.val(), 10) || null,
            price: this._parsePrice(this.ad.input.price.value),
            escrow_car_vin: this.ad.input.vin.$.val(),
            escrow_car_plate: this.ad.input.plate.$.val(),
            escrow_car_brand_id: parseInt(this.ad.input.brand.$.val(), 10) || null,
            escrow_car_model_year: parseInt(this.ad.input.year.$.val(), 10) || null,
            escrow_ad_sale_img: this.ad.input.fileLicence.value || null,
        };
        
        if (this.wizard && this.wizard.sellerId) {
            params.escrow_owner_id = this.wizard.sellerId;
        }

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
        const item_id = ev?.currentTarget?.dataset?.itemId || 0;

        this.state.id = id ? parseInt(id, 10) : 0;
        this.state.item_id = item_id ? parseInt(item_id, 10) : 0;

        const value = this.values.ads[id];
        /*if (value && value.owner_id && !value.seller_name) {
            this._loadSellerInfoForSidebar(id, value.owner_id);
        }*/
        const $item = $('.escrow-ad-sidebar-items');
        if ($item.length) {
            $item.find('.escrow-ad-item-name').text(value.name);
            $item.find('.escrow-ad-item-categ').text(value.categ);
            $item.find('.seller-name').text(value.partner || 'Not specified');
            $item.find('.seller-tc').text(value.vat || 'Not specified');
            $item.find('.seller-iban').text(value.iban || 'Not specified');
            
            const brandModel = value.brand ? `${value.brand} ` : 'Not specified';
            $item.find('.escrow-ad-item-brand-model').text(brandModel);
            $item.find('.escrow-ad-item-year').text(value.year || 'Not specified');
            $item.find('.escrow-ad-item-plate').text(value.plate || 'Not specified');
            $item.find('.escrow-ad-item-vin').text(value.vin || 'Not specified');

            let stateClass, stateLabel;
            if (value.state === 'new') {
                stateClass = 'success';
                stateLabel = _t('New');
            } else if (value.state === 'sold') {
                stateClass = 'danger';
                stateLabel = _t('Sold');
            } else {
                stateClass = 'info';
                stateLabel = _t('Waiting Approval');
            }

            $item.find('.escrow-ad-item-state').html(`<span class="${stateClass}">${stateLabel}</span>`);
            $item.find('.escrow-ad-item-price').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
            if (value.residual_amount !== undefined) {
                $('#remainingBalance').text(format.currency(value.residual_amount, this.currency.position, this.currency.symbol, this.currency.decimal));
            }
        } else {
            $item.find('.seller-name, .seller-tc, .seller-iban').text('Not specified');
            $item.find('.vehicle-year, .vehicle-plate, .vehicle-vin').text('Not specified');
            $item.find('.escrow-ad-item-price').text('');
            $item.find('.escrow-ad-item-state').html('');
            $item.find('.escrow-ad-item-name').text(_t('No ad found'));
            $item.find('.escrow-ad-item-categ').text('');
        }

        const $src = $(ev.currentTarget);
        if ($src.length) {
            const adData = {
                vin: $src.data('vin') || '',
                plate: $src.data('plate') || '',
                brand_id: String($src.data('brand-id') || ''),
                brand_name: $src.data('brand-name') || '',
                year: String($src.data('model-year') || ''),
                category_name: $src.data('category-name') || ''
            };

            if (adData.vin) this.ad.input.vin.$.val(adData.vin);
            if (adData.plate) this.ad.input.plate.$.val(adData.plate);

            let categSet = false;
            const $categNode = $src.find('[name=categ]');
            const catId = String($categNode.data('id') || '');
            
            if (catId) {
                this.ad.input.category.$.val(catId);
                categSet = true;
            } else if (adData.category_name) {
                const $options = this.ad.input.category.$.find('option');
                $options.each((i, e) => {
                    if ($(e).text().trim().toLowerCase() === adData.category_name.toLowerCase()) {
                        this.ad.input.category.$.val($(e).val());
                        categSet = true;
                        return false;
                    }
                });
            }

            if (adData.brand_id && this.ad.input.brand.$.find('option[value="' + adData.brand_id + '"]').length) {
                this.ad.input.brand.$.val(adData.brand_id);
                this.ad.input.brand.$.trigger('change');
            } else if (adData.brand_name) {
                const $brandOpt = this.ad.input.brand.$.find('option').filter((i, e) => $(e).text().trim() === adData.brand_name);
                if ($brandOpt.length) {
                    this.ad.input.brand.$.val($brandOpt.val());
                    this.ad.input.brand.$.trigger('change');
                }
            }
            
            if (adData.year) {
                this.ad.input.year.$.val(adData.year);
            }
        }
    },

    _prepareAd: function (id) {
        if (id) {
            this.state.id = parseInt(id);
            const ad = this.values.ads[id];
            this.ad.input.name.value = ad.name;
            this.ad.input.categ.value = ad.categ[0];
            this.ad.input.price.value = format.float(ad.price);
            //setTimeout(() => this.ad.input.img.value = ad.img, 1000);

        } else {
            this.state.id = 0;
            this.ad.input.name.value = '';
            this.ad.input.categ.value = '';
            this.ad.input.price.value = format.float(0);
            //this.ad.input.img.reset();
        }
    },

    _onClickWizardClose: function () {
        this._onChangeStep(this.wizard.currentStep - 1);
    },

    _onChangeStep: function (step, options={}) {
        if (step < 0 || step > 5) {
            return;
        }

        if (step === 0) {
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
        }

        if (this.ad.sidebar.$.hasClass('show')) {
            this._onClickButtonSidebarToggle();
        }

        this._setState({ step });
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

    _handleStepSpecificActions: function(stepNumber, options, stateId) {
        switch(stepNumber) {
            case 1:
                if (!this.state.id) {
                    for (const input of Object.values(this.seller.input)) {
                        input.value = null;
                    }
                } else {
                    this._initializeSellerInfoForm(stateId);
                }
                break;
                
            case 2:
                this._initializeProductInfoForm(stateId);
                break;
                
            case 3:
                this._initializeCustomerInfoForm(stateId);
                break;
                
            case 4:
                this._initializePaymentForm(stateId);
                if (options.paymentCompleted) {
                    console.log('test')
                    $('.payment-panel').addClass('d-none');
                    $('#payment_type').addClass('d-none');
                    this._showRemainingPaymentInfo();
                    
                    if (options.itemId) {
                        this._updatePaymentAmounts(options.itemId);
                    }
                }
                break;
                
            case 5:
                this._updatePaymentAmounts(options.itemId, stateId);
        }
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

        let values = {
            i: this.state.id,
            s: this.state.step,
        }
        let hash = btoa(JSON.stringify(values));
        let url = new URL(window.location); url.searchParams.set('', hash);
        window.history.replaceState({'': hash}, '', url);
        //window.location.hash = hash;
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
                    this.wizard.sellerId = result.partner_id;
                    this.displayNotification({
                        type: 'success',
                        title: 'Success',
                        message: 'Seller information saved',
                    });

                    return this._startOtp(result.partner_id).then((otpRes) => {
                        if (otpRes && otpRes.success) {
                            this.wizard.otpId = otpRes.otp_id;
                            this._showOtpModal(otpRes.expires_in || 120);
                        } else if (otpRes && otpRes.is_otp_verified) {
                            this.displayNotification({ type: 'info', title: 'OTP', message: 'OTP has already been verified.' });
                            this._markStepCompleted(this.wizard.currentStep);
                            this._onChangeStep(this.wizard.currentStep + 1);
                        } else {
                            this.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                        }
                    }).finally(() => {
                        this._enableWizard();
                    });

                } else {
                    this.displayNotification({
                        type: 'danger',
                        title: 'Error',
                        message: result.message || 'An error occurred while saving seller information.',
                    });
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
            for (const input of Object.values(this.ad.input)) {
                let valid = await input.validate();
                if (!valid) {
                    return this.displayNotification({
                        title: 'Error',
                        message: 'An error occurred while saving ad information.',
                        type: 'warning',
                    });
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

                    this.displayNotification({
                        type: 'success',
                        title: 'Success',
                        message: result.message || 'Product information has been saved.',
                    });
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
                    return this._startOtp(result.partner_id).then((otpRes) => {
                        if (otpRes && otpRes.success) {
                            this.wizard.otpId = otpRes.otp_id;
                            this._showOtpModal({ expiresIn: otpRes.expires_in || 120 });
                            this.displayNotification({
                                type: 'success',
                                title: 'Success',
                                message: result.message || 'Customer information saved. A verification code has been sent.',
                            });
                        } else if (otpRes && otpRes.is_otp_verified) {
                            this.displayNotification({ type: 'info', title: 'OTP', message: 'OTP has already been verified.' });
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
                    message: 'Connection error occurred.',
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
        if (this.state.id > 0) {
            this._prefillSellerFromAd(this.values.ads[this.state.id]);
        }
    },

    _initializeProductInfoForm: function () {
        if (this.state.id > 0) {
            this._getProductData();
            this._prefillProductFromAd(this.values.ads[this.state.id]);
        }
    },

    _initializeCustomerInfoForm: function () {
        console.log('test')
        this._bindRecipientToggle();
    },

    _initializePaymentForm: function () {
        this._updatePaymentAmounts(this.state.item_id);
    },

    _getProductData: function() {
        const self = this;
        this._rpc({
            route: '/get/ad',
            params: { ad_id: self.state.id },
        }).then((product) => {
            if (product && product.success) {
                self.values.ads[product.ad.id] = {
                    id: product.ad.id,
                    img: product.ad.image,
                    name: product.ad.name,
                    categ: product.ad.categ,
                    price: product.ad.price,
                    //state: product.ad.state,
                    owner_id: product.ad.owner_id,
                    customer_id: product.ad.customer_id,
                    vin: product.ad.vin,
                    plate: product.ad.plate,
                    brand_id: product.ad.brand_id,
                    brand_name: product.ad.brand_name,
                    year: product.ad.year,
                    item_id: product.ad.item_id,
                    amount: product.ad.amount,
                    residual_amount: product.ad.residual_amount,
                    paid_amount: product.ad.paid_amount,
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

            // Section toggle
            if ($ind.length) $ind.toggleClass('d-none', !isInd).toggle(isInd);
            if ($cor.length) $cor.toggleClass('d-none', isInd).toggle(!isInd);

            // Radio toggle
            if ($radioInd.length) $radioInd.prop('checked', isInd);
            if ($radioCor.length) $radioCor.prop('checked', !isInd);

            // Button toggle
            if ($btnInd.length && $btnCor.length) {
                $btnInd
                    .toggleClass('btn-dark active', isInd)
                    .toggleClass('btn-outline-dark', !isInd);
                $btnCor
                    .toggleClass('btn-dark active', !isInd)
                    .toggleClass('btn-outline-dark', isInd);
            }

            // Slider
            if ($slider.length) {
                $slider.css('transform', isInd ? 'translateX(0%)' : 'translateX(100%)');
            }
        }

        // Eski eventleri temizle
        $btnInd.off('click.userTypeToggle');
        $btnCor.off('click.userTypeToggle');
        $radioInd.off('change.userTypeToggle');
        $radioCor.off('change.userTypeToggle');

        // Yeni eventler
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

        // Başlangıçta seçili radio’ya göre ayarla
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
            };
        }
        return this._rpc({
            route: '/my/seller/save',
            params: formData,
        });
    },

    _startOtp: function(partnerId){
        return this._rpc({ route: '/my/otp/start', params: { partner_id: partnerId } });
    },

    _verifyOtp: function(code){
        return this._rpc({ route: '/my/otp/verify', params: { otp_id: this.wizard.otpId, code: code } });
    },

    _showOtpModal: function(expiresOrOpts){
        const self = this;
        const isObj = typeof expiresOrOpts === 'object' && expiresOrOpts !== null;
        const ttl = isObj ? (expiresOrOpts.expiresIn || expiresOrOpts.ttl || 120) : (typeof expiresOrOpts === 'number' ? expiresOrOpts : 120);
        const modalHtml = `
            <div class="otp-modal" id="otpModal" style="position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.4);z-index:1050;">
              <div style="background:#fff;border-radius:12px;padding:24px;max-width:420px;width:90%;text-align:center;">
                <h4 style="margin-bottom:12px;">Cep Telefonu Doğrulama</h4>
                <p style="margin-bottom:16px;">Lütfen cep telefonunuza gelen 4 haneli doğrulama kodunu giriniz.</p>
                <div style="display:flex;gap:8px;justify-content:center;margin-bottom:12px;">
                  <input type="text" inputmode="numeric" maxlength="1" class="otp-inp form__control" style="width:48px;height:48px;text-align:center;font-size:20px;border:1px solid #DDD;border-radius:8px;" />
                  <input type="text" inputmode="numeric" maxlength="1" class="otp-inp form__control" style="width:48px;height:48px;text-align:center;font-size:20px;border:1px solid #DDD;border-radius:8px;" />
                  <input type="text" inputmode="numeric" maxlength="1" class="otp-inp form__control" style="width:48px;height:48px;text-align:center;font-size:20px;border:1px solid #DDD;border-radius:8px;" />
                  <input type="text" inputmode="numeric" maxlength="1" class="otp-inp form__control" style="width:48px;height:48px;text-align:center;font-size:20px;border:1px solid #DDD;border-radius:8px;" />
                </div>
                <div class="otp-timer" style="margin-bottom:16px;color:#666;">Kalan süre: <span id="otpTimer">${ttl}</span> saniye</div>
                <div style="display:flex;gap:8px;justify-content:center;">
                  <button id="otpSubmit" class="button button__dark button__medium">Doğrula</button>
                  <button id="otpCancel" class="button button__light button__medium">İptal</button>
                </div>
              </div>
            </div>`;

        $('body').append(modalHtml);

        const $modal = $('#otpModal');
        const $inputs = $modal.find('.otp-inp');
        const $timer = $modal.find('#otpTimer');
        let secs = ttl;

        $inputs.on('input', function(){
            this.value = this.value.replace(/\D/g,'').slice(0,1);
            if (this.value && this.nextElementSibling) this.nextElementSibling.focus();
        });
        $inputs.first().focus();

        const interval = setInterval(() => {
            secs -= 1;
            if (secs < 0) secs = 0;
            $timer.text(secs);
            if (secs === 0) {
                clearInterval(interval);
                $('#otpSubmit').prop('disabled', true).addClass('disabled');
            }
        }, 1000);

        function closeModal(){
            clearInterval(interval);
            $modal.remove();
        }

        $modal.on('click', '#otpCancel', function(e){ e.preventDefault(); closeModal(); });
        $modal.on('click', '#otpSubmit', function(e){
            e.preventDefault();
            const code = Array.from($inputs).map(i=>i.value).join('');
            if (code.length !== 4) {
                self.displayNotification({type:'warning', title:'OTP', message:'Lütfen 4 haneli kodu giriniz.'});
                return;
            }
            const verifyFn = self._verifyOtp.bind(self);
            verifyFn(code).then(res=>{
                if (res && res.success) {
                    closeModal();
                    self._markStepCompleted(self.wizard.currentStep);
                    self._onChangeStep(self.wizard.currentStep + 1);
                } else {
                    self.displayNotification({ type:'danger', title:'OTP', message: (res && res.message) || 'Doğrulama başarısız' });
                }
            }).catch(()=>{
                self.displayNotification({ type:'danger', title:'OTP', message:'Doğrulama sırasında hata oluştu' });
            });
        });
    },

    _saveCustomerInfo: function() {
        const self = this;
        const userType = $('input[name="userType"]:checked').val();
        const isCardHolderDifferent = $('#checkPoint').is(':checked');

        const data = {
            customer_type: userType,
            is_card_holder_different: isCardHolderDifferent,
            product_id: this.state.id,
        };

        if (isCardHolderDifferent) {

            data.customer_name_surname = this.customer.input.name.$.val();
            data.customer_identity = this.customer.input.tc.$.val();
            data.customer_phone = this.customer.input.phone_individual.$.val();
            data.customer_email = this.customer.input.email_individual.$.val();
            data.customer_address = this.customer.input.address_individual.$.val();
            if (this.wizard && this.wizard.customerID) {
                data.escrow_customer_id = this.wizard.customerID;
            }
        }

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
            data.customer_person = this.customer.input.person.$.val();
            data.customer_phone = this.customer.input.phone_corporate.$.val();
            data.customer_email = this.customer.input.email_corporate.$.val();
            data.customer_address = this.customer.input.address_corporate.$.val();
        }
        return this._rpc({
            route: '/my/customer/save',
            params: data,
        }).then((result) => {
            if (result.success && result.partner_id) {
                if (isCardHolderDifferent) {
                    self.wizard.cardHolderID = result.partner_id;
                } else {
                    self.wizard.customerID = result.partner_id;
                }
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

    _updatePaymentAmounts: function(itemId) {
        rpc.query({
            route: '/payment/escrow/transaction-data',
            params: { item_id: itemId }
        }).then(data => {
            if (data && !data.error) {
                this.payment.amount.previous.$.text(this._formatCurrency(data.previous_amount));
                this.payment.amount.remaining.$.text(this._formatCurrency(data.remaining_amount));
                this.payment.amount.total.$.text(this._formatCurrency(data.total_amount));
                this.payment.transaction.reference.$.text(data.transaction_reference);
                this.payment.transaction.date.$.text(data.transaction_date);
                if (data.transaction_status){
                    this.payment.transaction.status.$.text('Approved');
                } else {
                    this.payment.transaction.status.$.text('Pending');
                }

                const percentage = Math.round((data.previous_amount / data.total_amount) * 100);
                $('.progress-text').text(percentage + '%');
                const circumference = 219.8;
                const offset = circumference - (percentage / 100) * circumference;
                $('.progress-ring-fill').css('stroke-dashoffset', offset);
            }
            return data;
        }).catch(error => {
            console.error('Error fetching payment data:', error);
        });
    },

    _formatCurrency: function(amount) {
        if (!amount) return '0 TL';
        return new Intl.NumberFormat('tr-TR').format(amount) + ' TL';
    },

    _onToggleDifferentHolder: function(event) {
        const isChecked = event.target.checked;
        const $assignmentSection = this.assignment.form.section.$;
        const $infoSection = this.payment.different.info.container.$;
        
        if (isChecked) {
            $assignmentSection.slideDown(300);
            $infoSection.slideDown(300);
        } else {
            $assignmentSection.slideUp(300);
            $infoSection.slideUp(300);
        }
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

    _lookupCustomerByIdentity: function(identity, customerType) {
        const self = this;
        
        this._rpc({
            route: '/my/customer/lookup',
            params: {
                identity: identity,
                customer_type: customerType
            }
        }).then(function(result) {
            if (result && result.success && result.found) {
                const data = result.customer_data;
                if (customerType === 'individual') {
                    this.customer.input.name_surname.$.val(data.name || '');
                    this.customer.input.phone_individual.$.val(data.phone || '');
                    this.customer.input.email_individual.$.val(data.email || '');
                    this.customer.input.address_individual.$.val(data.address || '');
                    this.customer.input.identity.$.val(data.vat || '');
                    if (data.is_otp_verified) {
                            this.customer.input.phone_individual.check.$.removeClass('d-none');
                            this.customer.input.phone_individual.error.$.addClass('d-none');
                        } else {
                            this.customer.input.phone_individual.check.$.addClass('d-none');
                            this.customer.input.phone_individual.error.$.removeClass('d-none');
                        }
                } else {
                    this.customer.input.corporate_title.$.val(data.name || '');
                    this.customer.input.tax_number.$.val(data.vat || '');
                    this.customer.input.tax_office.$.val(data.tax_office || '');
                    this.customer.input.phone_corporate.$.val(data.phone || '');
                    this.customer.input.email_corporate.$.val(data.email || '');
                    this.customer.input.address_corporate.$.val(data.address || '');
                    if (data.is_otp_verified) {
                            this.customer.input.phone_corporate.check.$.removeClass('d-none');
                            this.customer.input.phone_corporate.error.$.addClass('d-none');
                        } else {
                            this.customer.input.phone_corporate.check.$.addClass('d-none');
                            this.customer.input.phone_corporate.error.$.removeClass('d-none');
                        }
                }
                self.displayNotification({
                    type: 'info',
                    title: 'Customer Found',
                    message: 'Customer information has been automatically filled from existing records.',
                    sticky: false
                });
            }
        }).catch(function(error) {
            console.error('Error looking up customer:', error);
        });
    },

});
