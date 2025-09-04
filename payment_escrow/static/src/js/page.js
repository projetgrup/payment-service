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
            })
        };

        this.state = {
            id: 0,
            item_id: 0,
            amount: 0,
            residual_amount: 0,
            paid_amount: 0,
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
                        if (mod == 'individual' ) {
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
                        if (mod == 'individual' ) {
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
                    mask: '000 000 0000',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.phone_individual;
                        let message = null;
                        let valid = true;
                        if (mod == 'individual' ) {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                    check: new fields.element(),
                    error: new fields.element()
                }),
                email_individual: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.email_individual;
                        let message = null;
                        let valid = true;
                        if (mod == 'individual' ) {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                const email_regex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
                                if (!field._.masked.isComplete || !email_regex.test(field.value)) {
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
                    mask: 'TR00 0000 0000 0000 0000 0000 00',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.iban_individual;
                        let message = null;
                        let valid = true;
                        if (mod == 'individual' ) {
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
                iban_name_individual: new fields.string({
                    mask: /^[A-Za-zığüşöçĞÜŞÖÇİ]+[A-Za-zığüşöçĞÜŞÖÇİ\s]*$/,
                    prepareChar: str => str.toLocaleUpperCase('tr-TR'),
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.iban_name_individual;
                        let message = null;
                        let valid = true;
                        if (mod == 'individual' ) {
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
                        if (mod == 'corporate' ) {
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
                        if (mod == 'corporate' ) {
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
                        if (mod == 'corporate' && !field.value) {
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
                        if (mod == 'corporate' ) {
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
                    mask: '000 000 0000',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.phone_corporate;
                        let message = null;
                        let valid = true;
                        if (mod == 'corporate' ) {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                    check: new fields.element(),
                    error: new fields.element()
                }),
                email_corporate: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.email_corporate;
                        let message = null;
                        let valid = true;
                        if (mod == 'corporate' ) {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                const email_regex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
                                if (!field._.masked.isComplete || !email_regex.test(field.value)) {
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
                    mask: 'TR00 0000 0000 0000 0000 0000 00',
                    validate: () => {
                        const mod = $('input[name="userType"]:checked').val();
                        const field = this.seller.input.iban_corporate;
                        let message = null;
                        let valid = true;
                        if (mod == 'corporate' ) {
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
                        if (mod == 'corporate' ) {
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
                        if (mod == 'individual' ) {
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
                        if (mod == 'individual' ) {
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
                    mask: '000 000 0000',
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.phone_individual;
                        let message = null;
                        let valid = true;
                        if (mod == 'individual' ) {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                    check: new fields.element(),
                    error: new fields.element()
                }),
                email_individual: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.email_individual;
                        let message = null;
                        let valid = true;
                        if (mod == 'individual' ) {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                const email_regex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
                                if (!field._.masked.isComplete || !email_regex.test(field.value)) {
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
                        if (mod == 'individual' && !field.value) {
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
                        if (mod == 'corporate' ) {
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
                        if (mod == 'corporate' ) {
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
                        if (mod == 'corporate' && !field.value) {
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
                        if (mod == 'corporate' ) {
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
                    mask: '000 000 0000',
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.phone_corporate;
                        let message = null;
                        let valid = true;
                        if (mod == 'corporate' ) {
                            if (!field._.masked.isComplete) {
                                message = _t('Phone number is required');
                                valid = false;
                            } 
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    },
                    check: new fields.element(),
                    error: new fields.element()
                }),
                email_corporate: new fields.string({
                    mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                    validate: () => {
                        const mod = $('input[name="customerUserType"]:checked').val();
                        const field = this.customer.input.email_corporate;
                        let message = null;
                        let valid = true;
                        if (mod == 'corporate' ) {
                            if (!field.value) {
                                message = _t('Email is required');
                                valid = false;
                            } else  {
                                const email_regex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
                                if (!field._.masked.isComplete || !email_regex.test(field.value)) {
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
                        if (mod == 'corporate' && !field.value) {
                            message = _t('Address is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
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
                /*img: new fields.file({
                    allowMultiple: true,
                    accept: 'image/*',
                    maxFileSize: '15MB',
                    maxFiles: 10,
                    labelIdle: 'Drag & drop images or <span class="filepond--label-action">Browse</span><br><small>Up to 10 images, max 5MB</small>',
                    imagePreviewHeight: 170,
                    // Preserve original aspect; avoid client-side downscaling
                    // imageCropAspectRatio: undefined,
                    imageResizeTargetWidth: 1920,
                    imageResizeUpscale: false,
                    imageTransformOutputQuality: 0.95,
                    stylePanelLayout: 'compact circle',
                    styleLoadIndicatorPosition: 'center bottom',
                    styleProgressIndicatorPosition: 'right bottom',
                    styleButtonRemoveItemPosition: 'left bottom',
                    styleButtonProcessItemPosition: 'right bottom',
                }),*/
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
                // id: new fields.integer(),
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
                year: new fields.selection({
                    validate: () => {
                        const field = this.ad.input.year;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('Year is required');
                            valid = false;
                        }
                        this._onFieldValid(field, valid, message);
                        return valid;
                    }
                }),
                vin: new fields.string({
                    validate: () => {
                        const field = this.ad.input.vin;
                        let message = null;
                        let valid = true;
                        if (!field.value) {
                            message = _t('VIN is required');
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
                                const email_regex = /^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$/;
                                if (!field._.masked.isComplete || !email_regex.test(field.value)) {
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

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);
            this._parseAds();
            this._bindWizardToggle();
            this._bindWizardSteps();
            this._checkSuccess();
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
            expanded += (code - 55).toString(); // 'A' → 10
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
        this.state.item_id = this.values.ads[id].item_id;
        if (id) {
            this._openSellerEditForCard(id, 'vehicle');
        }
    },

    _onToggleSellerHolder: function() {
        const id = this.state.id;
        if (id) {
            this._openSellerEditForCard(id, 'seller');
        }
    },

    _onFileChange: function(e) {
        const self = this;
        const files = e.target.files;
        if (files && files.length > 0) {
            const firstFile = files[0];
            self._clearImagePreview();
            self._setProductImage(firstFile);
        } else {
            self._clearImagePreview();
        }
    },

    _setProductImage: function(file) {
        if (!file || !file.type.startsWith('image/')) {
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            /*if (this.ad && this.ad.input && this.ad.input.img) {
                this.ad.input.img.value = e.target.result;
            }*/
            this._showImagePreview(e.target.result);
        };
        reader.readAsDataURL(file);
    },

    _showImagePreview: function(imageSrc) {
        const $label = $('label[for="wizard_file_input"]');
        if (!$label.length) return;
        $label.find('svg, span, #wizard_num_of_files').addClass('d-none');
        let $img = $label.find('img#wizard_image_preview');
        if (!$img.length) {
            $img = $('<img id="wizard_image_preview" alt="License Photo"/>')
                .css({
                    width: '100%',
                    height: 'auto',
                    display: 'block',
                    marginTop: '8px',
                    objectFit: 'contain'
                });
            $label.append($img);
        }
        $img.attr('src', imageSrc);
        $('#image-preview').remove();
    },

    _clearImagePreview: function() {
        const $label = $('label[for="wizard_file_input"]');
        if ($label.length) {
            $label.find('img#wizard_image_preview').remove();
            $label.find('svg, span, #wizard_num_of_files').removeClass('d-none');
        }
        $('#image-preview').remove();
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
                state: $this.find('.escrow-ad-item-state').html().trim(),
                ...values
            };
            $this.data('value', null);
            $this.attr('data-value', null);
        });
    },

    _setupFileUpload: function() {
        const $wiz = $('.escrow-wizard');
        const $fileInput = $wiz.find('#file-input');
        const $fileList = $wiz.find('#files-list');
        const $numOfFiles = $wiz.find('#num-of-files');

        if (!$fileInput.length || !$fileList.length || !$numOfFiles.length) return;

        $fileInput.on('change', () => {
            $fileList.empty();

            const files = $fileInput[0].files;
            $numOfFiles.text(`${files.length} files selected`);

            Array.from(files).forEach((file) => {
                const fileName = file.name;
                let fileSize = (file.size / 1024).toFixed(1);
                let fileSizeStr = `${fileSize} KB`;

                if (fileSize >= 1024) {
                    fileSize = (fileSize / 1024).toFixed(1);
                    fileSizeStr = `${fileSize} MB`;
                }

                const $listItem = $('<li></li>');
                $listItem.html(`<p>${fileName}</p><p>${fileSizeStr}</p>`);
                $fileList.append($listItem);
            });
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
        this._onChangeStep(1, { scratch: true });
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
                        if (owner.is_otp_verified) {
                            this.seller.input.phone_corporate.check.$.removeClass('d-none');
                            this.seller.input.phone_corporate.error.$.addClass('d-none');
                        } else {
                            this.seller.input.phone_corporate.check.$.addClass('d-none');
                            this.seller.input.phone_corporate.error.$.removeClass('d-none');
                        }
                    } else {
                        $wiz.find('input[name="userType"][value="individual"]').prop('checked', true);
                        this._bindWizardToggle();
                        this.seller.input.name.value = owner.name || '';
                        this.seller.input.tc.value = owner.vat || '';
                        this.seller.input.phone_individual.value = owner.phone || '';
                        this.seller.input.email_individual.value = owner.email || '';
                        if (owner.is_otp_verified) {
                            this.seller.input.phone_individual.check.$.removeClass('d-none');
                            this.seller.input.phone_individual.error.$.addClass('d-none');
                        } else {
                            this.seller.input.phone_individual.check.$.addClass('d-none');
                            this.seller.input.phone_individual.error.$.removeClass('d-none');
                        }
                    }
                    
                    if (owner.bank_ids && owner.bank_ids.length > 0) {
                        const bankAccount = owner.bank_ids[0];
                        this.seller.input.iban_corporate.value = this._formatIbanDisplay(bankAccount.acc_number);
                        this.seller.input.iban_individual.value = this._formatIbanDisplay(bankAccount.acc_number);
                        this.seller.input.iban_name_individual.value = bankAccount.api_merchant || owner.name;
                        this.seller.input.iban_name_corporate.value = bankAccount.api_merchant || owner.name;
                        if (owner.bank_ids[0].is_verified) {
                            this.seller.input.iban_name_individual.check.$.removeClass('d-none');
                            this.seller.input.iban_name_individual.error.$.addClass('d-none');
                        } else {
                            this.seller.input.iban_name_individual.check.$.addClass('d-none');
                            this.seller.input.iban_name_individual.error.$.removeClass('d-none');
                        }
                    }
                    
                }
                return Promise.resolve();
            }).catch(() => {
                console.warn('Could not load owner data for prefill');
            });
        }
    },

    _loadSellerInfoForSidebar: function(adId, ownerId) {
        const self = this;
        
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
        
        if (adData.vin) this.ad.input.vin.$.val(adData.vin);
        if (adData.plate) this.ad.input.plate.$.val(adData.plate);
        
        if (adData.brand_id) {
            this.ad.input.brand.$.val(adData.brand_id);
            this.ad.input.brand.$.trigger('change');
        }
        if (adData.year) {
            this.ad.input.year.$.val(adData.year);
        }

        /*if (adData.img) {
            let src = adData.img;
            if (typeof src === 'string' && !src.startsWith('data:image/')) {
                src = 'data:image/png;base64,' + src;
            }
            if (this.ad && this.ad.input && this.ad.input.img) {
                this.ad.input.img.value = src;
            }
            this._showImagePreview(src);
        }*/
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
            //image_1920: this.ad.input.img.value || null
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

            $item.find('.escrow-ad-item-price').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
            $item.find('.escrow-ad-item-state').html(value.state);
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
        const step = this.wizard.currentStep;
        if (step > 1) {
            this._onChangeStep(step - 1);
        } else {
            this.seller.wizard.$.fadeOut(200, () => {
                $('.header').removeClass('header__steps');
                this.seller.ads.$.fadeIn(200);
            });
        }
    },

    _bindWizardSteps: function () {
        if (!$('.steps').length) return;
        this.wizard = {
            currentStep: this._getCurrentStepFromURL() || 1,
            previousStep: 1
        };

    },

    _getCurrentStepFromURL: function () {
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        return step ? parseInt(step) : null;
    },

    _onChangeStep: function(stepNumber, options = {}, stateId) {
        if (stepNumber < 1 || stepNumber > 5) {
            console.error('Invalid step number:', stepNumber);
            return;
        }

        $('.header').addClass('header__steps');

        this.wizard.previousStep = this.wizard.currentStep;
        this.wizard.currentStep = stepNumber;
        this._ensureWizardVisible();
        this._updateStepHeaders(stepNumber, options);
        this._showStepContent(stepNumber);
        this._handleStepSpecificActions(stepNumber, options, stateId);
        
        if (!options.skipUrlUpdate) {
            this._updateURL(stepNumber);
        }
    },

    _ensureWizardVisible: function() {
        if (this.ad.sidebar.$.hasClass('show')) {
            this._onClickButtonSidebarToggle();
        }

        if (this.seller.ads.$.css('display') !== 'none') {
            this.seller.ads.$.fadeOut(200, () => {
                this.seller.wizard.$.fadeIn(200);
            });
        }
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
        $('.wizard-step').fadeOut(200, () => {
            $(`.wizard-step-${stepNumber}`).fadeIn(200);
        });
    },

    _handleStepSpecificActions: function(stepNumber, options, stateId) {
        switch(stepNumber) {
            case 1:
                if (options.scratch) {
                    for (const input of Object.values(this.seller.input)) {
                        input.$.val(null);
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

    _updateURL: function (stepNumber) {
        const url = new URL(window.location);
        url.searchParams.set('step', stepNumber);
        window.history.pushState({step: stepNumber}, '', url);
    },

    _nextStep: function () {
        const self = this;
        if (this.wizard.currentStep === 1) {
            for (const input of Object.values(this.seller.input)) {
                let valid = input.validate();
                if (!valid) {
                    return self.displayNotification({
                        title: 'Error',
                        message: 'An error occurred while saving seller information.',
                        type: 'warning',
                    });
                }
            }
            this._saveSellerInfo().then(function(result) {
                if (result.success && result.partner_id) {
                    self.wizard.sellerId = result.partner_id;

                    self.displayNotification({
                        type: 'success',
                        title: 'Success',
                        message: 'Seller information saved',
                    });

                    return self._startOtp(result.partner_id).then((otpRes) => {
                        if (otpRes && otpRes.success) {
                            self.wizard.otpId = otpRes.otp_id;
                            self._showOtpModal(otpRes.expires_in || 120);
                            console.log('OTP started:', otpRes.otp_id);
                        } else if (otpRes && otpRes.is_otp_verified) {
                            self.displayNotification({ type: 'info', title: 'OTP', message: 'OTP has already been verified.' });
                            self._markStepCompleted(self.wizard.currentStep);
                            self._onChangeStep(self.wizard.currentStep + 1);
                            console.log('navigate')
                        } else {
                            self.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                        }
                    });

                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: 'Error',
                        message: result.message || 'An error occurred while saving seller information.',
                    });
                }
            }).catch(function(error) {
                self.displayNotification({
                    type: 'danger',
                    title: 'Error',
                    message: 'Connection error occurred.',
                });
                console.error('Error saving seller info:', error);
            });
        }

        if (this.wizard.currentStep === 2) {
            for (const input of Object.values(this.ad.input)) {
                let valid = input.validate();
                console.log('Validating input:', input, 'Result:', valid);
                if (!valid) {
                    return self.displayNotification({
                        title: 'Error',
                        message: 'An error occurred while saving ad information.',
                        type: 'warning',
                    });
                }
            }
            this._saveAdData().then(function(result) {
                if (result.success || result.id) {
                    if (result.id) {
                        self.state.id = result.id;
                        self.state.item_id = result.item_id;
                    }
                    self._markStepCompleted(self.wizard.currentStep);
                    self._onChangeStep(self.wizard.currentStep + 1);

                    self.displayNotification({
                        type: 'success',
                        title: 'Success',
                        message: result.message || 'Product information has been saved.',
                    });
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: 'Error',
                        message: result.message || 'Product information could not be saved.',
                    });
                }
            }).catch(function(error) {
                self.displayNotification({
                    type: 'danger',
                    title: 'Error',
                    message: 'Connection error occurred.',
                });
            });
            return false;
        }

        if (this.wizard.currentStep === 3) {
            for (const input of Object.values(this.customer.input)) {
                let valid = input.validate();
                console.log('Validating input:', input, 'Result:', valid);
                if (!valid) {
                    return self.displayNotification({
                        title: 'Error',
                        message: 'An error occurred while saving customer information.',
                        type: 'warning',
                    });
                }
            }
            this._saveCustomerInfo().then(function(result) {
                if (result.success && result.partner_id) {
                    return self._startOtp(result.partner_id).then(function(otpRes){
                        if (otpRes && otpRes.success) {
                            self.wizard.otpId = otpRes.otp_id;
                            self._showOtpModal({ expiresIn: otpRes.expires_in || 120 });
                            self.displayNotification({
                                type: 'success',
                                title: 'Success',
                                message: result.message || 'Customer information saved. A verification code has been sent.',
                            });
                        } else if (otpRes && otpRes.is_otp_verified) {
                            self.displayNotification({ type: 'info', title: 'OTP', message: 'OTP has already been verified.' });
                            self._markStepCompleted(self.wizard.currentStep);
                            self._onChangeStep(self.wizard.currentStep + 1);
                        } else {
                            self.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                        }
                    });
                } else if (result.success) {
                    self.displayNotification({ type: 'warning', title: 'Customer', message: 'Saved but verification could not start.' });
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: 'Error',
                        message: result.message || 'Customer Information could not be saved.',
                    });
                }
            }).catch(function(error) {
                self.displayNotification({
                    type: 'danger',
                    title: 'Error',
                    message: 'Connection error occurred.',
                });
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
        this._setupFileUpload();
        this._bindWizardToggle();
        if (this.state.id > 0) {
            this._prefillSellerFromAd(this.values.ads[this.state.id]);
        }
    },

    _initializeProductInfoForm: function () {
        this._setupFileUpload();
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
        this._setupFileUpload();
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
                    state: product.ad.state,
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

    _checkSuccess: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        const status = urlParams.get('status');
        const itemId = urlParams.get('item_id');
        const productId = urlParams.get('product_id');
        this.state.id = productId;
        this.state.item_id = itemId;

        if (step === '4' && status === 'completed') {
            this._onChangeStep(4, {
                paymentCompleted: true,
                markAsCompleted: true,
                itemId: itemId,
                skipUrlUpdate: true
            }, this.state.id);
        } else if (step === '5') {
            this._onChangeStep(5, {
                skipUrlUpdate: true,
                itemId: itemId
            }, this.state.id);
        }
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
        $wiz.find('#customer_name_surname').val('');
        $wiz.find('#customer_identity').val('');
        $wiz.find('#customer_phone_individual').val('');
        $wiz.find('#customer_email_individual').val('');
        $wiz.find('#customer_address_individual').val('');
        
        $wiz.find('#customer_corporate_title').val('');
        $wiz.find('#customer_tax_number').val('');
        $wiz.find('#customer_tax_office').val('');
        $wiz.find('#customer_person').val('');
        $wiz.find('#customer_phone_corporate').val('');
        $wiz.find('#customer_email_corporate').val('');
        $wiz.find('#customer_address_corporate').val('');
        
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
