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
        this.state = {
            id: 0,
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
        this.partner = new fields.integer({
            default: 0,
        });
        this.seller = {
            wizard: new fields.element(),
            button: {
                close: new fields.element({ events: [['click', this._onClickSellerClose]] }),
            },
            input: {
                // Individual seller fields
                name: new fields.string(), // namesurname
                tc: new fields.string(), // wizard_tckn
                birthdate: new fields.string(),
                phone_individual: new fields.string(),
                email_individual: new fields.string(),
                address_individual: new fields.string(),
                iban_individual: new fields.string(), // wizard_iban
                iban_name_individual: new fields.string(), // ibanaccountname_individual
                // Corporate seller fields
                corporate_title: new fields.string(),
                tax_number: new fields.string(), // wizard_tax
                tax_office: new fields.string(), // taxoffice
                corporate_person: new fields.string(),
                phone_corporate: new fields.string(),
                email_corporate: new fields.string(),
                address_corporate: new fields.string(),
                iban_corporate: new fields.string(), // wizard_iban_corp
                iban_name_corporate: new fields.string(), // ibanaccountname_corporate
            }
        };
        this.escrow = {
            input: {
                category: new fields.selection(),
                brand: new fields.selection(),
                model: new fields.selection(),
                year: new fields.selection(),
                name: new fields.string(),
                price: new fields.float({
                    mask: payloxPage.prototype._maskAmount.bind(this),
                    default: 0,
                }),
                desc: new fields.html({
                    parent: this,
                }),
                vin: new fields.string(),
                plate: new fields.string(),
            }
        }
        this.recipient = {
            input: {
                // Individual recipient fields
                name_surname: new fields.string(),
                identity: new fields.string(),
                birthdate: new fields.string(),
                phone_individual: new fields.string(),
                email_individual: new fields.string(),
                address_individual: new fields.string(),
                // Corporate recipient fields
                corporate_title: new fields.string(),
                tax_number: new fields.string(),
                tax_office: new fields.string(),
                person: new fields.string(),
                phone_corporate: new fields.string(),
                email_corporate: new fields.string(),
                address_corporate: new fields.string(),
            }
        }
        this.ad = {
            sidebar: new fields.element(),
            sideback: new fields.element({
                events: [['click', this._onClickSideback]],
            }),
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
                discard: new fields.element({
                    events: [['click', this._onClickButtonDiscard]],
                }),
                create: new fields.element({
                    events: [['click', this._onClickButtonCreate]],
                }),
                edit: new fields.element({
                    events: [['click', this._onClickButtonEdit]],
                }),
                save: new fields.element({
                    events: [['click', this._onClickButtonSave]],
                }),
                delete: new fields.element({
                    events: [['click', this._onClickButtonDelete]],
                }),
                continue: new fields.element({
                    events: [['click', this._onClickButtonContinue]],
                }),
            },
            input: {
                img: new fields.file({
                    allowMultiple: false,
                    accept: 'image/*',
                    maxFileSize: '5MB',
                }),
                name: new fields.string(),
                desc: new fields.html({
                    parent: this,
                }),
                categ: new fields.selection(),
                price: new fields.float({
                    mask: payloxPage.prototype._maskAmount.bind(this),
                    default: 0,
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
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);
            this._parseAds();
            this._bindWizardValidation();
            this._bindWizardToggle();
            this._bindWizardSteps();
            framework.hideLoading();
        });
    },

    _parseAds: function () {
        $('[field="ad.item"][data-value]').each((i, e) => {
            const $this = $(e);
            const categ = $this.find('.escrow-ad-item-categ');
            this.values.ads[e.dataset.id] = {
                id: $this.data('id'),
                img: $this.find('.escrow-ad-item-image img').attr('src'),
                name: $this.find('.escrow-ad-item-name').text().trim(),
                categ: [categ.data('id'), categ.text().trim()],
                price: parseFloat($this.find('.escrow-ad-item-price').data('value')),
                state: $this.find('.escrow-ad-item-state').html().trim(),
                desc: $this.find('.escrow-ad-item-desc').html().trim(),
                owner_id: $this.data('owner-id'),
                customer_id: $this.data('customer-id'),
                vin: $this.data('vin'),
                plate: $this.data('plate'),
                brand_id: $this.data('brand-id'),
                brand_name: $this.data('brand-name'),
                model_id: $this.data('model-id'),
                model_name: $this.data('model-name'),
                year: $this.data('model-year')
            };
        });
    },

    _formatTurkishCurrency: function(value, withCurrency) {
        if (withCurrency === undefined) withCurrency = false;
        if (!value && value !== 0) return '';
        const num = parseFloat(value);
        if (isNaN(num)) return '';
        const formatted = new Intl.NumberFormat('tr-TR').format(num);
        return withCurrency ? formatted + ' TL' : formatted;
    },

    _setupPartialPriceValidation: function() {
        const self = this;
        const $wiz = $('.escrow-wizard');
        const $form = $wiz.find('#partialPriceForm');
        const $input = $form.find('#paymentAmount');
        const $button = $form.find('#payAllBtn');
        const $balanceText = $form.find('#remainingBalance');

        if (!$form.length || !$input.length) return;

        const getRawValue = (val) => val.replace(/\D/g, '');

        const formatCurrency = (val) => {
            return self._formatTurkishCurrency(val, true);
        };

        $button.on('click', () => {
            const raw = getRawValue($balanceText.text());
            $input.val(formatCurrency(raw));
            $input.trigger('input');
            this._validatePartialPriceField();
        });

        $input.on('input', (e) => {
            const caretPos = $input[0].selectionStart;
            const raw = getRawValue($input.val());
            const formatted = formatCurrency(raw);

            $input.val(formatted);

            requestAnimationFrame(() => {
                if ($input[0].setSelectionRange) {
                    const newPos = Math.max(0, $input.val().length - 3); 
                    $input[0].setSelectionRange(newPos, newPos);
                }
            });
            this._validatePartialPriceField();
        });
    },

    _validatePartialPriceField: function() {
        const $wiz = $('.escrow-wizard');
        const $input = $wiz.find('#paymentAmount');
        const $group = $input.closest('.form__group');
        
        $input.removeClass('is-invalid -error just-validate-error-field');
        $group.find('.form__error-label, .just-validate-error-label').remove();

        const val = $input.val() || '';
        const getRawValue = (val) => val.replace(/\D/g, '');
        
        if (!val.trim()) {
            $input.addClass('is-invalid -error just-validate-error-field');
            const $errorDiv = $('<div class="form__error-label just-validate-error-label">Miktar zorunludur</div>');
            $group.append($errorDiv);
            return false;
        }

        const raw = parseInt(getRawValue(val), 10);
        if (isNaN(raw) || raw <= 0) {
            $input.addClass('is-invalid -error just-validate-error-field');
            const $errorDiv = $('<div class="form__error-label just-validate-error-label">0\'dan büyük bir miktar girin</div>');
            $group.append($errorDiv);
            return false;
        }

        return true;
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
            $numOfFiles.text(`${files.length} dosya seçildi`);

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

        $wiz.on('change', '.installment-table input[type="radio"]', (ev) => {
            const $row = $(ev.currentTarget).closest('.installment-table__row');
            const $table = $row.closest('.installment-table');
            $table.find('.installment-table__row').removeClass('active');
            $row.addClass('active');
        });
        $wiz.on('click', '.installment-table .installment-table__row', (ev) => {
            const $row = $(ev.currentTarget);
            const $radio = $row.find('input[type="radio"]');
            if ($radio.length) {
                $radio.prop('checked', true).trigger('change');
            }
        });

        function bindValidCheck(selector, testFn) {
            const $input = $wiz.find(selector);
            const $check = $input.siblings('.state-check');
            $input.on('input blur', () => {
                const val = ($input.val() || '').trim();
                const ok = testFn(val);
                $input.toggleClass('is-valid', ok);
                $check.toggleClass('d-none', !ok);
            });
        }

        bindValidCheck('#wizard_vin', (v) => v.replace(/[^0-9A-Za-z]/g, '').length >= 8);
        bindValidCheck('#wizard_plate', (v) => v.trim().length >= 5);

        $wiz.on('change', '#wizard_brand', (ev) => {
            const brandId = String($(ev.currentTarget).val() || '');
            const $model = $wiz.find('#wizard_model');
            const $opts = $model.find('option');
            $opts.each((i, e) => {
                const $e = $(e);
                const bid = String($e.data('brand') || '');
                if (!$e.val()) return;
                const hide = !!brandId && bid !== brandId;
                $e.prop('disabled', hide);
                if (hide) {
                    $e.attr('hidden', 'hidden');
                } else {
                    $e.removeAttr('hidden');
                }
            });
            const current = $model.val();
            if (current) {
                const $sel = $model.find('option[value="' + current + '"]');
                if ($sel.is(':disabled') || $sel.is('[hidden]')) $model.val('');
            }
        });
    },

    _updateAds: function (value) {
        if (this.state.id) {
            Object.assign(this.values.ads[value.id], {
                img: value.img,
                name: value.name,
                categ: value.categ,
                price: value.price,
                desc: value.desc,
            });

            const $items = this.ad.item.$.filter(`[data-id=${value.id}]`);
            if ($items.length) {
                $items.find('[name=name]').text(value.name);
                $items.find('[name=categ]').text(value.categ[1]).data('id', value.categ[0]);
                $items.find('[name=price]').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
                $items.find('[name=desc]').html(value.desc);
                $items.find('[name=img]').attr('src', value.img);
            }

            this.state.id = 0;

        } else {
            this.values.ads[value.id] = {
                id: value.id,
                img: value.img,
                name: value.name,
                categ: value.categ,
                price: value.price,
                desc: value.desc,
                state: '-',
            };

            const $items = this.ad.item.$.filter(`[data-id=${value.id}]`);
            if ($items.length) {
                $items.find('[name=name]').text(value.name);
                $items.find('[name=categ]').text(value.categ[1]).data('id', value.categ[0]);
                $items.find('[name=price]').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
                $items.find('[name=desc]').html(value.desc);
                $items.find('[name=img]').attr('src', value.img);
            }

            $('.escrow-ad-list-header').after(qweb.render('paylox.escrow.list.item', { ad: value, currency: this.currency, format }));
            $('.escrow-ad-grid-container').prepend(qweb.render('paylox.escrow.grid.item', { ad: value, currency: this.currency, format }));
        }
    },

    _deleteAds: function (id) {
        delete this.values.ads[id];
        this.ad.item.$.filter(`[data-id=${id}]`).remove();
        this._onClickSideback();
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

    _onClickSideback: function () {
        this._onClickButtonSidebarToggle();
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

    _onClickButtonDiscard: function () {
    this._prepareAd();
        this._activateView('list');
    },

    _onClickButtonCreate: function (ev) {
        this._prepareAd();
        this._openSellerSheet();
    },

    _onClickButtonEdit: function (ev) {
        const adId = $(ev.currentTarget).data('id');
        this._prepareAd(adId);
        
        this._closeSidebar();
        
        this._openSellerWizardForEdit(adId);
    },

    _closeSidebar: function() {
        $('.escrow-ad-wrapper').removeClass('blur');
        $('.escrow-ad-sidebar-section').addClass('d-none');
        this.ad.sideback.$.addClass('d-none');
        this.ad.sidebar.$.removeClass('show');
    },

    _openSellerWizardForEdit: function(adId) {
        const self = this;
        
        $('.escrow-ad-read').addClass('d-none');
        
        this.wizard = {
            currentStep: 1,
            previousStep: 1,
            editMode: true,
            editingAdId: adId
        };
        
        if (adId && this.values.ads[adId]) {
            const adData = this.values.ads[adId];
            
            this._prefillSellerFromAd(adData);
            
            this._prefillProductFromAd(adData);
            
            this._prefillRecipientFromAd(adData);
        }
        
        this._updateStepStates();
        this._showStepContent(1);
        this._updateNavigationButtons(1);
        this._navigateToStep(2);
        
        this.seller.wizard.$.removeClass('d-none').hide().fadeIn(200);
    },

    _prefillSellerFromAd: function(adData) {
        const $wiz = $('.escrow-wizard');
        
        if (adData.owner_id) {
            this._rpc({
                route: '/my/partner/get',
                params: { partner_id: adData.owner_id }
            }).then((ownerData) => {
                
                console.log(ownerData)
                if (ownerData.success) {
                    const owner = ownerData.partner;
                    if (owner.is_company) {
                        $wiz.find('input[name="userType"][value="corporate"]').prop('checked', true);
                        this._bindWizardToggle();
                        
                        $wiz.find('#corporate_title').val(owner.name || '');
                        $wiz.find('#wizard_tax').val(owner.vat || '');
                        $wiz.find('#taxoffice').val(owner.commercial_partner_id?.name || '');
                        $wiz.find('#corporate_person').val(owner.name || '');
                        $wiz.find('#phone_corporate').val(owner.phone || '');
                        $wiz.find('#email_corporate').val(owner.email || '');
                        $wiz.find('#address_corporate').val(this._formatAddress(owner));
                    } else {
                        $wiz.find('input[name="userType"][value="individual"]').prop('checked', true);
                        this._bindWizardToggle();
                        
                        $wiz.find('#namesurname').val(owner.name || '');
                        $wiz.find('#wizard_tckn').val(owner.vat || '');
                        $wiz.find('#birthdate').val(''); 
                        $wiz.find('#phone_individual').val(owner.phone || '');
                        $wiz.find('#email_individual').val(owner.email || '');
                        $wiz.find('#address_individual').val(this._formatAddress(owner));
                    }
                    
                    if (owner.bank_ids && owner.bank_ids.length > 0) {
                        const bankAccount = owner.bank_ids[0];
                        $wiz.find('#wizard_iban, #wizard_iban_corp').val(this._formatIban(bankAccount.acc_number));
                        $wiz.find('#ibanaccountname_individual, #ibanaccountname_corporate').val(bankAccount.api_merchant || owner.name);
                    }
                }
            }).catch(() => {
                console.warn('Could not load owner data for prefill');
            });
        }
    },

    _prefillProductFromAd: function(adData) {
        if (adData.name) this.escrow.input.name.$.val(adData.name);
        if (adData.price) this.escrow.input.price.$.val(adData.price);
        if (adData.description) this.escrow.input.desc.$.val(adData.description);
        
        if (adData.categ_id) {
            this.escrow.input.category.$.val(adData.categ_id);
        }
        
        if (adData.vin) this.escrow.input.vin.$.val(adData.vin);
        if (adData.plate) this.escrow.input.plate.$.val(adData.plate);
        
        if (adData.brand_id) {
            this.escrow.input.brand.$.val(adData.brand_id);
            this.escrow.input.brand.$.trigger('change');
        }
        if (adData.model_id) {
            this.escrow.input.model.$.val(adData.model_id);
        }
        if (adData.year) {
            this.escrow.input.year.$.val(adData.year);
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

    _formatIban: function(iban) {
        if (!iban) return '';
        const cleanIban = iban.replace(/\s/g, '');
        if (cleanIban.length >= 26) {
            return cleanIban.substring(0, 4) + ' ' +
                   cleanIban.substring(4, 8) + ' ' +
                   cleanIban.substring(8, 12) + ' ' +
                   cleanIban.substring(12, 16) + ' ' +
                   cleanIban.substring(16, 20) + ' ' +
                   cleanIban.substring(20, 24) + ' ' +
                   cleanIban.substring(24);
        }
        return cleanIban;
    },

    _prefillRecipientFromAd: function(adData) {
        const $wiz = $('.escrow-wizard');
        
        if (adData.customer_id) {
            this._rpc({
                route: '/my/partner/get',
                params: { partner_id: adData.customer_id }
            }).then((customerData) => {
                if (customerData.success) {
                    const customer = customerData.partner;
                    if (customer.is_company) {
                        $wiz.find('input[name="recipientType"][value="corporate"]').prop('checked', true);
                        this._bindRecipientToggle();
                        $wiz.find('#recipient_corporate_title').val(customer.name || '');
                        $wiz.find('#recipient_tax_number').val(customer.vat || '');
                        $wiz.find('#recipient_tax_office').val(customer.commercial_partner_id?.name || '');
                        $wiz.find('#recipient_person').val(customer.comment?.replace('Yetkili Kişi: ', '') || '');
                        $wiz.find('#recipient_phone_corporate').val(customer.phone || '');
                        $wiz.find('#recipient_email_corporate').val(customer.email || '');
                        $wiz.find('#recipient_address_corporate').val(customer.street || '');
                    } else {
                        $wiz.find('input[name="recipientType"][value="individual"]').prop('checked', true);
                        this._bindRecipientToggle();
                        
                        $wiz.find('#recipient_name_surname').val(customer.name || '');
                        $wiz.find('#recipient_identity').val(customer.vat || '');
                        $wiz.find('#recipient_birthdate').val(customer.comment?.replace('Doğum Tarihi: ', '') || '');
                        $wiz.find('#recipient_phone_individual').val(customer.phone || '');
                        $wiz.find('#recipient_email_individual').val(customer.email || '');
                        $wiz.find('#recipient_address_individual').val(customer.street || '');
                    }
                }
            }).catch(() => {
                console.warn('Could not load customer data for prefill');
            });
        }
    },

    _onClickButtonSave: function (ev) {
        framework.showLoading();
        let params = {
            id: this.state.id,
            name: this.ad.input.name.value,
            categ: [this.ad.input.categ.value, this.ad.input.categ.text],
            price: this.ad.input.price.value,
            desc: this.ad.input.desc.value,
            img: this.ad.input.img.value,
        }
        rpc.query({ route: '/my/ad/save', params }).then((result) => {
            if ('error' in result) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('An error occured.') + ' ' + result.error,
                });
            } else {
                params.id = result.id;
                this._updateAds(params);
                this._activateView('list');
                this.displayNotification({
                    type: 'success',
                    title: _t('Success'),
                    message: this.state.id ? _t('Ad has been added.') : _t('Ad has been saved.'),
                });
            }
        }).guardedCatch(() => {
            this.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please contact with your system administrator.'),
            });
        }).finally(() => {
            framework.hideLoading();
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

    _onClickButtonContinue: function (ev) {
        const id = parseInt($(ev.currentTarget).data('id'));
        if (!id) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please select an ad first.'),
            });
            return;
        }
        this._openSellerSheet(id);
    },

    _onClickAd: function (ev) {
        this._onClickButtonSidebarToggle({ currentTarget: { dataset: { value: 'items'}}});

        const id = ev?.currentTarget?.dataset?.id;
        const value = this.values.ads[id];
        const $item = $('.escrow-ad-sidebar-items');
        if ($item.length) {
            $item.find('.escrow-ad-item-img').attr('src', value.img);
            $item.find('.escrow-ad-item-name').text(value.name);
            $item.find('.escrow-ad-item-categ').text(value.categ[1]);
            $item.find('.escrow-ad-item-price').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
            $item.find('.escrow-ad-item-state').html(value.state);
            $item.find('.escrow-ad-item-desc').html(value.desc);
            $item.find('.escrow-ad-button-edit').data('id', id);
            $item.find('.escrow-ad-button-delete').data('id', id);
            $item.find('.escrow-ad-button-continue').data('id', id);
        } else {
            $item.find('.escrow-ad-item-img').attr('src', '/payment_jetcheckout/static/src/img/placeholder.png');
            $item.find('.escrow-ad-item-name').text(_t('No ad found'));
            $item.find('.escrow-ad-item-categ').text('');
            $item.find('.escrow-ad-item-price').text('');
            $item.find('.escrow-ad-item-state').html('');
            $item.find('.escrow-ad-item-desc').html('');
            $item.find('.escrow-ad-button-edit').data('id', 0);
            $item.find('.escrow-ad-button-delete').data('id', 0);
            $item.find('.escrow-ad-button-continue').data('id', 0);
        }

        const $src = $(ev.currentTarget);
        if ($src.length) {
            const adData = {
                vin: $src.data('vin') || '',
                plate: $src.data('plate') || '',
                brand_id: String($src.data('brand-id') || ''),
                brand_name: $src.data('brand-name') || '',
                model_id: String($src.data('model-id') || ''),
                model_name: $src.data('model-name') || '',
                year: String($src.data('model-year') || ''),
                category_name: $src.data('category-name') || ''
            };

            if (adData.vin) this.escrow.input.vin.$.val(adData.vin);
            if (adData.plate) this.escrow.input.plate.$.val(adData.plate);
            
            let categSet = false;
            const $categNode = $src.find('[name=categ]');
            const catId = String($categNode.data('id') || '');
            
            if (catId) {
                this.escrow.input.category.$.val(catId);
                categSet = true;
            } else if (adData.category_name) {
                const $options = this.escrow.input.category.$.find('option');
                $options.each((i, e) => {
                    if ($(e).text().trim().toLowerCase() === adData.category_name.toLowerCase()) {
                        this.escrow.input.category.$.val($(e).val());
                        categSet = true;
                        return false;
                    }
                });
            }
            
            if (adData.brand_id && this.escrow.input.brand.$.find('option[value="' + adData.brand_id + '"]').length) {
                this.escrow.input.brand.$.val(adData.brand_id);
                this.escrow.input.brand.$.trigger('change');
            } else if (adData.brand_name) {
                const $brandOpt = this.escrow.input.brand.$.find('option').filter((i, e) => $(e).text().trim() === adData.brand_name);
                if ($brandOpt.length) {
                    this.escrow.input.brand.$.val($brandOpt.val());
                    this.escrow.input.brand.$.trigger('change');
                }
            }
            
            if (adData.model_id && this.escrow.input.model.$.find('option[value="' + adData.model_id + '"]').length) {
                this.escrow.input.model.$.val(adData.model_id);
            } else if (adData.model_name) {
                const $modelOpt = this.escrow.input.model.$.find('option').filter((i, e) => $(e).text().trim() === adData.model_name);
                if ($modelOpt.length) {
                    this.escrow.input.model.$.val($modelOpt.val());
                }
            }
            
            if (adData.year) {
                this.escrow.input.year.$.val(adData.year);
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
            this.ad.input.desc.value = ad.desc;
            setTimeout(() => this.ad.input.img.value = ad.img, 1000);
        } else {
            this.state.id = 0;
            this.ad.input.name.value = '';
            this.ad.input.categ.value = '';
            this.ad.input.price.value = format.float(0);
            this.ad.input.desc.value = '';
            this.ad.input.img.reset();
        }
    },

    _openSellerSheet: function (id) {
        if (this.ad.sidebar.$.hasClass('show')) {
            this._onClickButtonSidebarToggle();
        }
        this.seller.wizard.$.removeClass('d-none').hide().fadeIn(200);
        $('.escrow-ad-read').hide();

        const $wiz = $('.escrow-wizard');
        const $step1 = $wiz.find('.wizard-step-1');
        const $step2 = $wiz.find('.wizard-step-2');
        const $step3 = $wiz.find('.wizard-step-3');
        $step1.removeClass('d-none');
        $step2.addClass('d-none');
        $step3.addClass('d-none');
        const $steps = $wiz.find('.escrow-wizard-header .step.bullet');
        $steps.removeClass('active completed');
        $steps.find('.check').addClass('d-none');
        $steps.find('.num').removeClass('d-none');
        $steps.eq(0).addClass('active');

        if (!this.wizard) {
            this.wizard = {
                currentStep: 1,
                previousStep: 1
            };
        } else {
            this.wizard.currentStep = 1;
            this.wizard.previousStep = 1;
        }
        
        this._updateStepStates();
    },

    _onClickSellerClose: function () {
        const wasEditMode = this.wizard && this.wizard.editMode;
        
        if (this.wizard) {
            this.wizard.editMode = false;
            this.wizard.editingAdId = null;
        }
        
        this.seller.wizard.$.fadeOut(200, () => {
            this.seller.wizard.$.addClass('d-none');
            
            if (wasEditMode) {
                $('.escrow-ad-read').removeClass('d-none').fadeIn(200);
            } else {
                $('.escrow-ad-read').fadeIn(200);
            }
            
            this._clearWizardForm();
        });
    },

    _clearWizardForm: function() {
        const $wiz = $('.escrow-wizard');
        
        $wiz.find('input[type="text"], input[type="email"], textarea').val('');
        $wiz.find('select').prop('selectedIndex', 0);
        
        $wiz.find('input[name="userType"][value="individual"]').prop('checked', true);
        
        // Reset steps to step 1
        this.wizard = {
            currentStep: 1,
            previousStep: 1,
            editMode: false,
            editingAdId: null
        };
        
        this._updateStepStates();
        this._showStepContent(1);
        this._updateNavigationButtons(1);
    },

    _completeWizard: function() {
        const self = this;
        
        if (this.wizard && this.wizard.editMode) {
            this._updateExistingAd().then(() => {
                this.displayNotification({
                    type: 'success',
                    title: 'Başarılı',
                    message: 'İlan bilgileri başarıyla güncellendi.',
                });
                
                setTimeout(() => {
                    self._onClickSellerClose();
                    self._loadAds();
                }, 1500);
            }).catch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: 'Hata',
                    message: 'İlan güncellenirken bir hata oluştu: ' + (error.message || 'Bilinmeyen hata'),
                });
            });
        } else {
            this._saveWizardData().then(() => {
                this.displayNotification({
                    type: 'success',
                    title: 'Başarılı',
                    message: 'Tüm bilgiler kaydedildi. Ödeme sayfasına yönlendiriliyorsunuz.',
                });
                
                setTimeout(() => {
                    self._onClickSellerClose();
                }, 1500);
            }).catch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: 'Hata',
                    message: 'Bilgiler kaydedilirken bir hata oluştu: ' + (error.message || 'Bilinmeyen hata'),
                });
            });
        }
    },

    _saveWizardData: function() {
        const self = this;
        
        return new Promise((resolve, reject) => {
            const sellerData = this._getSellerFormData();
            
            this._rpc({
                route: '/my/seller/save',
                params: sellerData
            }).then((sellerResult) => {
                if (!sellerResult.success) {
                    reject(new Error(sellerResult.message || 'Seller kayıt hatası'));
                    return;
                }
                
                const productData = this._getProductFormData();
                productData.owner_id = sellerResult.partner_id;
                
                return self._rpc({
                    route: '/my/ad/save',
                    params: productData
                });
            }).then((productResult) => {
                if (productResult && productResult.error) {
                    reject(new Error(productResult.error));
                } else {
                    resolve(productResult);
                }
            }).catch((error) => {
                reject(error);
            });
        });
    },

    _updateExistingAd: function() {
        const self = this;
        
        return new Promise((resolve, reject) => {
            const sellerData = this._getSellerFormData();
            const adId = this.wizard.editingAdId;
            
            if (!adId) {
                reject(new Error('Güncellenecek ilan bulunamadı'));
                return;
            }
            
            const adData = this.values.ads[adId];
            const ownerId = adData ? adData.owner_id : null;
            
            if (ownerId) {
                console.log('Updating existing owner:', ownerId);
            }
            
            const productData = this._getProductFormData();
            productData.id = adId;
            if (ownerId) {
                productData.owner_id = ownerId;
            }
            
            self._rpc({
                route: '/my/ad/save',
                params: productData
            }).then((result) => {
                if (result && result.error) {
                    reject(new Error(result.error));
                } else {
                    resolve(result);
                }
            }).catch((error) => {
                reject(error);
            });
        });
    },

    _getSellerFormData: function() {
        const $wiz = $('.escrow-wizard');
        const userType = $wiz.find('input[name="userType"]:checked').val();
        
        const sellerData = {
            seller_type: userType
        };
        
        if (userType === 'corporate') {
            sellerData.seller_name = this.seller.input.corporate_title.$.val();
            sellerData.seller_tax_number = this.seller.input.tax_number.$.val();
            sellerData.seller_contact_person = this.seller.input.corporate_person.$.val();
            sellerData.seller_phone = this.seller.input.phone_corporate.$.val();
            sellerData.seller_email = this.seller.input.email_corporate.$.val();
            sellerData.seller_iban = this.seller.input.iban_corporate.$.val();
            sellerData.seller_iban_name = this.seller.input.iban_name_corporate.$.val();
        } else {
            sellerData.seller_name = this.seller.input.name.$.val();
            sellerData.seller_tc_number = this.seller.input.tc.$.val();
            sellerData.seller_birthdate = this.seller.input.birthdate.$.val();
            sellerData.seller_phone = this.seller.input.phone_individual.$.val();
            sellerData.seller_email = this.seller.input.email_individual.$.val();
            sellerData.seller_iban = this.seller.input.iban_individual.$.val();
            sellerData.seller_iban_name = this.seller.input.iban_name_individual.$.val();
        }
        
        return sellerData;
    },

    _getProductFormData: function() {
        const productData = {
            id: null,
            name: this.escrow.input.name.$.val(),
            categ: [this.escrow.input.category.$.val(), this.escrow.input.category.$.find('option:selected').text()],
            price: this._parseTurkishPrice(this.escrow.input.price.$.val()),
            desc: this.escrow.input.desc.$.val(),
            vin: this.escrow.input.vin.$.val(),
            plate: this.escrow.input.plate.$.val(),
            brand_id: this.escrow.input.brand.$.val(),
            model_id: this.escrow.input.model.$.val(),
            year: this.escrow.input.year.$.val(),
            img: null // TODO: Handle image upload
        };
        
        if (this.wizard && this.wizard.sellerId) {
            productData.owner_id = this.wizard.sellerId;
        }
        
        return productData;
    },

    _loadAds: function() {
        window.location.reload();
    },

    _bindWizardValidation: function () {
        const self = this;
        const $wiz = $('.escrow-wizard');
        if (!$wiz.length) return;

        this.validationErrors = {};
        this.validationRules = {
            '#namesurname': [
                { rule: 'required', errorMessage: 'Ad Soyad zorunludur' }
            ],
            '#wizard_tckn': [
                { rule: 'required', errorMessage: 'T.C. Kimlik No zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^[1-9][0-9]{10}$/.test(val.replace(/\D/g, '')),
                    errorMessage: '11 haneli geçerli T.C. No girin'
                }
            ],
            '#birthdate': [
                { rule: 'required', errorMessage: 'Doğum tarihi zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^\d{2}\/\d{2}\/\d{4}$/.test(val),
                    errorMessage: 'GG/AA/YYYY formatında girin'
                }
            ],
            '#email_individual': [
                { rule: 'required', errorMessage: 'E-posta zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
                    errorMessage: 'Geçerli bir e-posta giriniz'
                }
            ],
            '#phone_individual': [
                { rule: 'required', errorMessage: 'Telefon zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9\s]{10,15}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Geçerli bir telefon giriniz'
                }
            ],
            '#wizard_iban': [
                { rule: 'required', errorMessage: 'IBAN zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^TR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}$/.test(val.replace(/\s/g, '')),
                    errorMessage: 'Geçerli bir IBAN giriniz'
                }
            ],
            '#ibanaccountname_individual': [
                { rule: 'required', errorMessage: 'Hesap adı zorunludur' }
            ],
            // Corporate fields
            '#corporate_title': [
                { rule: 'required', errorMessage: 'Firma unvanı zorunludur' }
            ],
            '#wizard_tax': [
                { rule: 'required', errorMessage: 'Vergi numarası zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9]{10}$/.test(val.replace(/\D/g, '')),
                    errorMessage: '10 haneli geçerli vergi no girin'
                }
            ],
            '#corporate_person': [
                { rule: 'required', errorMessage: 'Yetkili kişi adı zorunludur' }
            ],
            '#email_corporate': [
                { rule: 'required', errorMessage: 'E-posta zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val),
                    errorMessage: 'Geçerli bir e-posta giriniz'
                }
            ],
            '#phone_corporate': [
                { rule: 'required', errorMessage: 'Telefon zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9\s]{10,15}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Geçerli bir telefon giriniz'
                }
            ],
            '#wizard_iban_corp': [
                { rule: 'required', errorMessage: 'IBAN zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^TR\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}$/.test(val.replace(/\s/g, '')),
                    errorMessage: 'Geçerli bir IBAN giriniz'
                }
            ],
            '#ibanaccountname_corporate': [
                { rule: 'required', errorMessage: 'Hesap adı zorunludur' }
            ],
            '#wizard_category': [
                { rule: 'required', errorMessage: 'Satış kategorisi seçin' },
                {
                    rule: 'custom',
                    validator: (val) => val !== '' && val !== '0',
                    errorMessage: 'Lütfen satış kategorisi seçin'
                }
            ],
            '#wizard_price': [
                { rule: 'required', errorMessage: 'Satış fiyatı zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => {
                        return /^\d{1,3}(\.\d{3})*,\d{2}$/.test(val) || /^\d+,\d{2}$/.test(val) || /^\d+$/.test(val);
                    },
                    errorMessage: 'Geçerli bir fiyat girin (örn: 1.000.000,00)'
                },
                {
                    rule: 'custom',
                    validator: (val) => {
                        const numericValue = self._parseTurkishPrice(val);
                        return numericValue > 0;
                    },
                    errorMessage: 'Fiyat sıfırdan büyük olmalıdır'
                }
            ],
            '#wizard_vin': [
                { rule: 'required', errorMessage: 'Şase numarası zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^[A-HJ-NPR-Z0-9]{17}$/.test(val.toUpperCase()),
                    errorMessage: 'Geçerli bir 17 karakterlik VIN girin'
                },
                {
                    rule: 'custom',
                    validator: (val) => self._isValidVinChecksum(val.toUpperCase()),
                    errorMessage: 'Geçersiz VIN numarası (kontrol hanesi yanlış)'
                }
            ],
            '#wizard_plate': [
                { rule: 'required', errorMessage: 'Plaka zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^(0[1-9]|[1-7][0-9]|8[01])\s?[A-Z]{1,3}\s?[0-9]{1,4}$/.test(val),
                    errorMessage: 'Geçerli bir plaka girin (örn: 34 ABC 123)'
                }
            ],
            '#wizard_brand': [
                { rule: 'required', errorMessage: 'Marka seçin' },
                {
                    rule: 'custom',
                    validator: (val) => val !== '' && val !== '0',
                    errorMessage: 'Marka seçin'
                }
            ],
            '#wizard_model': [
                { rule: 'required', errorMessage: 'Model seçin' },
                {
                    rule: 'custom',
                    validator: (val) => val !== '' && val !== '0',
                    errorMessage: 'Model seçin'
                }
            ],
            '#wizard_year': [
                { rule: 'required', errorMessage: 'Yıl zorunludur' },
                {
                    rule: 'custom',
                    validator: (val) => /^\d{4}$/.test(val),
                    errorMessage: 'Yıl sadece sayı olmalıdır'
                },
                {
                    rule: 'custom',
                    validator: (val) => {
                        const year = parseInt(val);
                        return year >= 1950 && year <= new Date().getFullYear();
                    },
                    errorMessage: 'Geçerli bir yıl girin'
                }
            ],
            '#wizard_file_input': [
                {
                    rule: 'custom',
                    validator: () => {
                        const input = $wiz.find('#wizard_file_input')[0];
                        return input && input.files && input.files.length > 0;
                    },
                    errorMessage: 'En az bir dosya seçmelisiniz'
                }
            ]
        };

        const validateField = (selector, showError = true) => {
            const $field = $wiz.find(selector);
            if (!$field.length) return true;

            const value = $field.val() || '';
            const rules = this.validationRules[selector] || [];
            
            $field.removeClass('is-invalid -error just-validate-error-field -success');
            const $group = $field.closest('.form__group');
            $group.find('.form__error-label, .just-validate-error-label').remove();
            $group.find('.state-check').addClass('d-none');
            $group.find('.form__error').addClass('d-none');

            // Check each rule
            for (const rule of rules) {
                let isValid = true;
                let errorMessage = rule.errorMessage;

                if (rule.rule === 'required') {
                    isValid = value.trim() !== '';
                } else if (rule.rule === 'custom' && rule.validator) {
                    isValid = rule.validator(value);
                }

                if (!isValid) {
                    if (showError) {
                        $field.addClass('is-invalid -error just-validate-error-field');
                        const $errorDiv = $(`<div class="form__error-label just-validate-error-label">${errorMessage}</div>`);
                        $group.append($errorDiv);
                    }
                    return false;
                }
            }

            if (value.trim() !== '') {
                $field.addClass('-success');
                $group.find('.state-check').removeClass('d-none');
            }

            return true;
        };

        this.getCurrentMode = () => {
            return !$wiz.find('.wizard-section-individual').hasClass('d-none') ? 'individual' : 'corporate';
        };

        Object.keys(this.validationRules).forEach(selector => {
            const $field = $wiz.find(selector);
            if ($field.length) {
                $field.on('input blur', () => {
                    const mode = self.getCurrentMode();
                    const isIndividualField = selector.includes('individual') || selector === '#namesurname' || 
                                             selector === '#wizard_tckn' || selector === '#birthdate' || 
                                             selector === '#wizard_iban' || selector === '#ibanaccountname_individual';
                    const isCorporateField = selector.includes('corporate') || selector === '#corporate_title' || 
                                           selector === '#wizard_tax' || selector === '#corporate_person' ||
                                           selector === '#wizard_iban_corp' || selector === '#ibanaccountname_corporate';
                    const isProductField = selector.includes('#wizard_') && !selector.includes('_iban') && !selector.includes('_tckn') && !selector.includes('_tax');

                    if ((mode === 'individual' && isIndividualField) || 
                        (mode === 'corporate' && isCorporateField) || 
                        isProductField) {
                        setTimeout(() => validateField(selector), 100);
                    }
                });
            }
        });

        const setupIBANFormatting = (selector) => {
            const $iban = $wiz.find(selector);

            $iban.on('input', function() {
                const cursorPos = this.selectionStart;
                let value = $(this).val();
                
                let cleanValue = value.replace(/[^A-Z0-9]/gi, '').toUpperCase();
                
                if (cleanValue.length > 0 && !cleanValue.startsWith('TR')) {
                    cleanValue = 'TR' + cleanValue;
                } else if (cleanValue.length === 0) {
                    cleanValue = 'TR';
                }
                
                if (cleanValue.length > 26) {
                    cleanValue = cleanValue.substring(0, 26);
                }
                
                let formattedValue = '';
                for (let i = 0; i < cleanValue.length; i++) {
                    if (i === 4 || i === 8 || i === 12 || i === 16 || i === 20 || i === 24) {
                        formattedValue += ' ';
                    }
                    formattedValue += cleanValue[i];
                }
                
                $(this).val(formattedValue);
                
                let newCursorPos = cursorPos;
                
                if (value.length === 0 || (!value.toUpperCase().startsWith('TR') && cleanValue.startsWith('TR'))) {
                    newCursorPos = Math.max(2, cursorPos);
                }
                
                const spacesBeforeCursor = formattedValue.substring(0, newCursorPos).split(' ').length - 1;
                newCursorPos = Math.min(newCursorPos + spacesBeforeCursor, formattedValue.length);
                
                if (this.setSelectionRange) {
                    setTimeout(() => {
                        this.setSelectionRange(newCursorPos, newCursorPos);
                    }, 0);
                }
            });

            $iban.on('focus', function() {
                const value = $(this).val().trim();
                if (!value) {
                    $(this).val('TR');
                    setTimeout(() => {
                        if (this.setSelectionRange) {
                            this.setSelectionRange(2, 2);
                        }
                    }, 0);
                }
            });

            $iban.on('keydown', function(e) {
                const cursorPos = this.selectionStart;
                const value = $(this).val();
                
                if ((e.key === 'Backspace' || e.key === 'Delete') && cursorPos <= 2) {
                    e.preventDefault();
                }
            });
        };

        setupIBANFormatting('#wizard_iban');
        setupIBANFormatting('#wizard_iban_corp');

        $wiz.find('#corporate_title').on('input', function() {
            const cursorPos = this.selectionStart;
            const oldValue = $(this).val();
            const newValue = oldValue.toUpperCase();
            $(this).val(newValue);
            
            if (this.setSelectionRange) {
                this.setSelectionRange(cursorPos, cursorPos);
            }
        });

        $wiz.find('#wizard_plate').on('input', function() {
            const cursorPos = this.selectionStart;
            const oldValue = $(this).val();
            const newValue = oldValue.toUpperCase();
            $(this).val(newValue);
            
            if (this.setSelectionRange) {
                this.setSelectionRange(cursorPos, cursorPos);
            }
        });

        $wiz.find('#wizard_vin').on('input', function() {
            const cursorPos = this.selectionStart;
            const oldValue = $(this).val();
            const newValue = oldValue.toUpperCase();
            $(this).val(newValue);
            
            if (this.setSelectionRange) {
                this.setSelectionRange(cursorPos, cursorPos);
            }
        });

        $wiz.find('#wizard_file_input').on('change', function() {
            const files = this.files;
            const $filesList = $('#wizard_files_list');
            const $counter = $('#wizard_num_of_files');
            
            if (files.length > 0) {
                $counter.text(`${files.length} dosya seçildi`);
                $filesList.empty();
                
                Array.from(files).forEach((file, index) => {
                    $filesList.append(`<li>${file.name}</li>`);
                });
            } else {
                $counter.text('Hiçbir Görsel Seçilmedi');
                $filesList.empty();
            }
            
            const selector = '#wizard_file_input';
            if (self.validationRules[selector]) {
                setTimeout(() => validateField(selector), 100);
            }
        });

        this.validateWizardStep1 = () => {
            const mode = this.getCurrentMode();
            let isValid = true;

            if (mode === 'individual') {
                const fields = ['#namesurname', '#wizard_tckn', '#birthdate', '#email_individual', '#phone_individual', '#wizard_iban', '#ibanaccountname_individual'];
                fields.forEach(selector => {
                    if (!validateField(selector)) {
                        isValid = false;
                    }
                });
            } else {
                const fields = ['#corporate_title', '#wizard_tax', '#corporate_person', '#email_corporate', '#phone_corporate', '#wizard_iban_corp', '#ibanaccountname_corporate'];
                fields.forEach(selector => {
                    if (!validateField(selector)) {
                        isValid = false;
                    }
                });
            }

            return isValid;
        };
        this.validateWizardStep2 = () => {
            let isValid = true;
            const fields = ['#wizard_category', '#wizard_price', '#wizard_vin', '#wizard_plate', '#wizard_brand', '#wizard_model', '#wizard_year', '#wizard_file_input'];
            
            fields.forEach(selector => {
                if (!validateField(selector)) {
                    isValid = false;
                }
            });

            return isValid;
        };
    },

    _bindWizardSteps: function () {
        const self = this;
        if (!$('.steps').length) return;

        this.wizard = {
            currentStep: this._getCurrentStepFromURL() || 1,
            previousStep: 1
        };

        this._updateStepStates();

        $(document).on('click', '.steps__content a[data-step]', function (ev) {
            ev.preventDefault();
            const step = parseInt($(this).data('step'));
            self._navigateToStep(step);
        });

        $(document).on('click', '.steps__item:not(.-active)', function (ev) {
            ev.preventDefault();
            const $stepItem = $(this);
            const stepNumber = $stepItem.index() + 1;
            
            if ($stepItem.hasClass('-completed') || stepNumber === self.wizard.currentStep + 1) {
                self._navigateToStep(stepNumber);
            }
        });

        $(document).on('click', '[data-wizard-action="next"]', function (ev) {
            ev.preventDefault();
            self._nextStep();
        });

        $(document).on('click', '[data-wizard-action="prev"]', function (ev) {
            ev.preventDefault();
            self._previousStep();
        });

        $(document).on('click', '[data-wizard-action="submit"]', function (ev) {
            ev.preventDefault();
            if (!self._validateAllSteps()) {
                self.displayNotification({
                    type: 'warning',
                    title: 'Uyarı',
                    message: 'Lütfen tüm adımlardaki gerekli alanları doğru şekilde doldurunuz.',
                });
                return false;
            }
            
            self._completeWizard();
        });
    },

    _getCurrentStepFromURL: function () {
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        return step ? parseInt(step) : null;
    },

    _navigateToStep: function (stepNumber) {
        if (stepNumber < 1 || stepNumber > 5) {
            return;
        }

        this.wizard.previousStep = this.wizard.currentStep;
        this.wizard.currentStep = stepNumber;
        
        this._updateURL(stepNumber);
        
        this._updateStepStates();
        
        this._showStepContent(stepNumber);
        
        this._updateNavigationButtons(stepNumber);
        
        this._performStepActions(stepNumber);
    },

    _updateURL: function (stepNumber) {
        const url = new URL(window.location);
        url.searchParams.set('step', stepNumber);
        window.history.pushState({step: stepNumber}, '', url);
    },

    _updateStepStates: function () {
        const self = this;
        $('.steps__item').each(function (index) {
            const $stepItem = $(this);
            const stepNumber = index + 1;
            
            $stepItem.removeClass('-active -completed');
            
            if (stepNumber < self.wizard.currentStep) {
                $stepItem.addClass('-completed');
            } else if (stepNumber === self.wizard.currentStep) {
                $stepItem.addClass('-active');
            }
        });
    },

    _showStepContent: function (stepNumber) {
        $('.wizard-step').addClass('d-none');
        
        $(`.wizard-step-${stepNumber}`).removeClass('d-none');
    },

    _updateNavigationButtons: function (currentStep) {
        const $prevBtn = $('[data-wizard-action="prev"]');
        const $nextBtn = $('[data-wizard-action="next"]');
        const $submitBtn = $('[data-wizard-action="submit"]');
        
        $prevBtn.toggle(currentStep > 1);
        
        if (currentStep === 5) {
            $nextBtn.hide();
            $submitBtn.show();
        } else {
            $nextBtn.show();
            $submitBtn.hide();
        }
    },

    _performStepActions: function (currentStep) {
        switch (currentStep) {
            case 1:
                this._initializeSellerInfoForm();
                break;
            case 2:
                this._initializeProductInfoForm();
                break;
            case 3:
                this._initializeRecipientInfoForm();
                break;
            case 4:
                this._initializePaymentForm();
                break;
            case 5:
                this._showCompletionPage();
                break;
        }
    },

    _nextStep: function () {
        const self = this;
        
        if (!this._validateCurrentStep()) {
            this.displayNotification({
                type: 'warning',
                title: 'Uyarı',
                message: 'Lütfen tüm gerekli alanları doğru şekilde doldurunuz.',
            });
            return false;
        }

        if (this.wizard.currentStep === 1) {
            this._saveSellerInfo().then(function(result) {
                if (result.success) {
                    self._markStepCompleted(self.wizard.currentStep);
                    self._navigateToStep(self.wizard.currentStep + 1);
                    
                    self.displayNotification({
                        type: 'success',
                        title: 'Başarılı',
                        message: result.message || 'Satıcı bilgileri kaydedildi.',
                    });
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: 'Hata',
                        message: result.message || 'Satıcı bilgileri kaydedilirken bir hata oluştu.',
                    });
                }
            }).catch(function(error) {
                self.displayNotification({
                    type: 'danger',
                    title: 'Hata',
                    message: 'Bağlantı hatası oluştu.',
                });
            });
            return false; // Prevent default navigation
        }

        // If moving from step 2 to step 3, save product information (both edit and new mode)
        if (this.wizard.currentStep === 2) {
            this._saveProductInfo().then(function(result) {
                if (result.success || result.id) {
                    // Save the product ID for future use (e.g., recipient save)
                    if (result.id && !self.wizard.editMode) {
                        self.wizard.savedProductId = result.id;
                    }
                    
                    // Mark current step as completed
                    self._markStepCompleted(self.wizard.currentStep);
                    self._navigateToStep(self.wizard.currentStep + 1);
                    
                    self.displayNotification({
                        type: 'success',
                        title: 'Başarılı',
                        message: result.message || 'Ürün bilgileri kaydedildi.',
                    });
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: 'Hata',
                        message: result.message || 'Ürün bilgileri kaydedilirken bir hata oluştu.',
                    });
                }
            }).catch(function(error) {
                self.displayNotification({
                    type: 'danger',
                    title: 'Hata',
                    message: 'Bağlantı hatası oluştu.',
                });
            });
            return false; // Prevent default navigation
        }

        // If moving from step 3 to step 4, save recipient information
        if (this.wizard.currentStep === 3) {
            this._saveRecipientInfo().then(function(result) {
                if (result.success) {
                    // Mark current step as completed
                    self._markStepCompleted(self.wizard.currentStep);
                    self._navigateToStep(self.wizard.currentStep + 1);
                    
                    self.displayNotification({
                        type: 'success',
                        title: 'Başarılı',
                        message: result.message || 'Alıcı bilgileri kaydedildi.',
                    });
                } else {
                    self.displayNotification({
                        type: 'danger',
                        title: 'Hata',
                        message: result.message || 'Alıcı bilgileri kaydedilirken bir hata oluştu.',
                    });
                }
            }).catch(function(error) {
                self.displayNotification({
                    type: 'danger',
                    title: 'Hata',
                    message: 'Bağlantı hatası oluştu.',
                });
            });
            return false; // Prevent default navigation
        }

        if (this.wizard.currentStep < 5) {
            // Mark current step as completed
            this._markStepCompleted(this.wizard.currentStep);
            this._navigateToStep(this.wizard.currentStep + 1);
        }
        return true;
    },

    _previousStep: function () {
        if (this.wizard.currentStep > 1) {
            this._navigateToStep(this.wizard.currentStep - 1);
        }
    },

    _validateCurrentStep: function () {
        const currentStep = this.wizard.currentStep;
        
        switch (currentStep) {
            case 1:
                return this.validateWizardStep1();
            case 2:
                return this._validateProductInfo();
            case 3:
                return this._validateRecipientInfo();
            case 4:
                return this._validatePaymentInfo();
            default:
                return true;
        }
    },

    _validateAllSteps: function () {
        // Validate all steps before final submission
        return this.validateWizardStep1() && 
               this._validateProductInfo() && 
               this._validateRecipientInfo() &&
               this._validatePaymentInfo();
    },

    _validateProductInfo: function () {
        // Use the new validation system for Step 2
        return this.validateWizardStep2();
    },

    _validatePaymentInfo: function () {
        // Payment info validation logic
        const $wiz = $('.escrow-wizard');
        let isValid = true;

        // Clear all previous errors
        $wiz.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $wiz.find('.form__error-label, .just-validate-error-label').remove();

        // Helper function to show error
        const showError = ($field, message) => {
            $field.addClass('is-invalid -error just-validate-error-field');
            const $group = $field.closest('.form__group');
            const $errorDiv = $(`<div class="form__error-label just-validate-error-label">${message}</div>`);
            $group.append($errorDiv);
            isValid = false;
        };

        // Card holder name validation
        const $cardHolder = $wiz.find('#card_holder_name');
        if ($cardHolder.length) {
            const cardHolderValue = $cardHolder.val().trim();
            if (!cardHolderValue) {
                showError($cardHolder, 'Kart sahibi adı zorunludur');
            } else if (cardHolderValue.length < 3) {
                showError($cardHolder, 'Kart sahibi adı en az 3 karakter olmalıdır');
            }
        }

        // Card number validation
        const $cardNumber = $wiz.find('#card_number');
        if ($cardNumber.length) {
            const cardNumberValue = $cardNumber.val().replace(/\D/g, '');
            if (!cardNumberValue) {
                showError($cardNumber, 'Kart numarası zorunludur');
            } else if (cardNumberValue.length < 16) {
                showError($cardNumber, 'Geçerli bir kart numarası giriniz');
            }
        }

        // Card expiry validation
        const $cardExpiry = $wiz.find('#card_expiry');
        if ($cardExpiry.length) {
            const expiryValue = $cardExpiry.val().trim();
            if (!expiryValue) {
                showError($cardExpiry, 'Son kullanma tarihi zorunludur');
            } else if (!/^\d{2}\/\d{2}$/.test(expiryValue)) {
                showError($cardExpiry, 'AA/YY formatında giriniz');
            }
        }

        // CVV validation
        const $cvv = $wiz.find('#cvv');
        if ($cvv.length) {
            const cvvValue = $cvv.val().replace(/\D/g, '');
            if (!cvvValue) {
                showError($cvv, 'Güvenlik kodu zorunludur');
            } else if (cvvValue.length < 3) {
                showError($cvv, 'Güvenlik kodu en az 3 haneli olmalıdır');
            }
        }

        // Payment amount validation (if exists)
        const paymentAmountValid = this._validatePartialPriceField();
        if (!paymentAmountValid) {
            isValid = false;
        }

        // Agreement checkboxes validation
        const $agreement = $wiz.find('#agreementChk');
        if ($agreement.length && !$agreement.is(':checked')) {
            // Show error for agreement checkbox
            const $agreementLabel = $agreement.closest('label');
            $agreementLabel.addClass('text-danger');
            $agreementLabel.after('<div class="form__error-label just-validate-error-label">Sözleşmeyi kabul etmeniz gerekiyor</div>');
            isValid = false;
        }

        return isValid;
    },

    _initializeSellerInfoForm: function () {
        // Seller info form initialization
        this._setupFileUpload();
    },

    _initializeProductInfoForm: function () {
        // Product info form initialization
        this._setupFileUpload();
        this._setupPriceFormatting();
    },

    _setupPriceFormatting: function() {
        const $wiz = $('.escrow-wizard');
        const $priceInput = $wiz.find('#wizard_price');
        
        if (!$priceInput.length) return;
        
        const self = this;
        
        // Turkish price formatting function
        const formatTurkishPrice = (value) => {
            // Remove all non-digits
            let numericValue = value.replace(/[^\d]/g, '');
            
            // If empty, return empty
            if (!numericValue) return '';
            
            // Convert to integer for processing
            let num = parseInt(numericValue, 10);
            
            // Format with thousands separator (dots) and add decimal part (,00)
            let formattedValue = num.toLocaleString('tr-TR').replace(/,/g, '.');
            
            // Add ,00 for decimal part
            formattedValue += ',00';
            
            return formattedValue;
        };
        
        // Format price input on input
        $priceInput.on('input', function() {
            const currentValue = $(this).val();
            const cursorPosition = this.selectionStart;
            const formattedValue = formatTurkishPrice(currentValue);
            
            if (formattedValue !== currentValue) {
                $(this).val(formattedValue);
                // Try to maintain cursor position
                const newPosition = Math.min(cursorPosition, formattedValue.length);
                this.setSelectionRange(newPosition, newPosition);
            }
            
            // Update remaining balance when price changes
            self._updateRemainingBalance(formattedValue);
        });
        
        // Also format on blur to ensure consistency
        $priceInput.on('blur', function() {
            const currentValue = $(this).val();
            if (currentValue && !currentValue.includes(',')) {
                const formattedValue = formatTurkishPrice(currentValue);
                $(this).val(formattedValue);
                self._updateRemainingBalance(formattedValue);
            }
        });
    },

    _updateRemainingBalance: function(priceValue) {
        const $remainingBalance = $('.escrow-wizard #remainingBalance');
        if (!$remainingBalance.length || !priceValue) return;
        
        // Parse the Turkish formatted price and format it for display
        const numericPrice = this._parseTurkishPrice(priceValue);
        if (numericPrice > 0) {
            const formattedPrice = this._formatTurkishCurrency(numericPrice, true);
            $remainingBalance.text(formattedPrice);
        }
    },

    // Utility function to convert Turkish formatted price to numeric
    _parseTurkishPrice: function(formattedPrice) {
        if (!formattedPrice) return 0;
        console.log('Parsing Turkish price:', formattedPrice);
        
        return parseFloat(formattedPrice.replace(/\./g, '').replace(',', '.')) || 0;
    },

    // Utility function to format numeric price to Turkish format
    _formatTurkishPrice: function(numericPrice) {
        if (!numericPrice && numericPrice !== 0) return '';
        let formattedValue = Math.floor(numericPrice).toLocaleString('tr-TR').replace(/,/g, '.');
        formattedValue += ',00';
        return formattedValue;
    },

    _initializePaymentForm: function () {
        // Payment form initialization
        this._setupRemainingBalanceFromProduct();
        this._setupPartialPriceValidation();
        this._setupFileUpload();
        this._setupCreditCardInstallments();
    },

    _setupRemainingBalanceFromProduct: function() {
        const $wiz = $('.escrow-wizard');
        const $priceInput = $wiz.find('#wizard_price');
        const $remainingBalance = $wiz.find('#remainingBalance');
        
        if (!$priceInput.length || !$remainingBalance.length) return;
        
        // Get the product price from wizard step 2
        const priceValue = $priceInput.val();
        if (priceValue) {
            // Parse the Turkish formatted price and format it for display
            const numericPrice = this._parseTurkishPrice(priceValue);
            const formattedPrice = this._formatTurkishCurrency(numericPrice, true);
            $remainingBalance.text(formattedPrice);
        }
    },

    _setupCreditCardInstallments: function() {
        const $wiz = $('.escrow-wizard');
        const $cardNumber = $wiz.find('#card_number');
        const $cardExpiry = $wiz.find('#card_expiry');
        const $cvv = $wiz.find('#cvv');
        const $installmentContainer = $wiz.find('#installmentOptionsContainer');
        
        if (!$cardNumber.length || !$installmentContainer.length) return;
        
        const self = this;
        
        // Function to check BIN and fetch installment options
        const checkBINAndFetchInstallments = (cardNumber) => {
            if (cardNumber.length >= 6) {
                const bin = cardNumber.substring(0, 6);
                $installmentContainer.slideDown(300);
            } else {
                $installmentContainer.slideUp(300);
            }
        };
        
        $cardExpiry.on('input', function() {
            let value = $(this).val().replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2, 4);
            }
            $(this).val(value);
        });
        
        $cardNumber.on('input', function() {
            let value = $(this).val().replace(/\D/g, '');
            if (value.length > 16) {
                value = value.slice(0, 16);
            }
            checkBINAndFetchInstallments(value);
            value = value.replace(/(\d{4})(?=\d)/g, '$1 ');
            $(this).val(value);
        });
        
        $cvv.on('input', function() {
            let value = $(this).val().replace(/\D/g, '');
            if (value.length > 4) {
                value = value.slice(0, 4);
            }
            $(this).val(value);
        });
    },

    _formatPriceForDisplay: function(price) {
        if (!price) return '0,00';
        price = price.replace('.', ',');
        const num = parseFloat(price);
        if (isNaN(num)) return '0,00';
        
        return num.toLocaleString('tr-TR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    },

    _showCompletionPage: function () {
        // Completion page actions
        console.log('Wizard completed');
    },

    _markStepCompleted: function (stepNumber) {
        if (stepNumber >= 1 && stepNumber <= 4) {
            const $stepItem = $(`.steps__item:nth-child(${stepNumber})`);
            $stepItem.addClass('-completed');
        }
    },

    _bindWizardToggle: function () {
        const $wiz = $('.escrow-wizard');
        if (!$wiz.length) return;
        const $btnInd = $wiz.find('[data-type="individual"]').parent();
        const $btnCor = $wiz.find('[data-type="corporate"]').parent();
        const $radioInd = $wiz.find('.radioTab__control[value="individual"]');
        const $radioCor = $wiz.find('.radioTab__control[value="corporate"]');
        const $secInd = $wiz.find('.wizard-section-individual');
        const $secCor = $wiz.find('.wizard-section-corporate');
        const $slider = $wiz.find('.radioTab__slider');

        function setMode(mode) {
            const isInd = mode === 'individual';
            
            // Update sections visibility
            $secInd.toggleClass('d-none', !isInd);
            $secCor.toggleClass('d-none', isInd);
            
            // Update radio buttons without triggering events
            if ($radioInd.length && $radioCor.length) {
                $radioInd.off('change');
                $radioCor.off('change');
                
                $radioInd.prop('checked', isInd);
                $radioCor.prop('checked', !isInd);
                
                // Re-bind events after updating
                $radioInd.on('change', () => {
                    if ($radioInd.is(':checked')) {
                        setMode('individual');
                    }
                });
                $radioCor.on('change', () => {
                    if ($radioCor.is(':checked')) {
                        setMode('corporate');
                    }
                });
            } else {
                // Button-based UI fallback
                $btnInd.toggleClass('btn-dark active', isInd).toggleClass('btn-outline-dark', !isInd);
                $btnCor.toggleClass('btn-outline-dark', isInd).toggleClass('btn-dark active', !isInd);
            }
            
            // Update slider position for animation
            if ($slider.length) {
                if (isInd) {
                    $slider.css('transform', 'translateX(0%)');
                } else {
                    $slider.css('transform', 'translateX(100%)');
                }
                $btnInd.toggleClass('btn-dark active', isInd);
                $btnCor.toggleClass('btn-outline-dark active', !isInd);
            }
        }

        // Bind button events
        $btnInd.on('click', (e) => { e.preventDefault(); setMode('individual'); });
        $btnCor.on('click', (e) => { e.preventDefault(); setMode('corporate'); });
        
        // Initial radio event binding
        $radioInd.on('change', () => {
            if ($radioInd.is(':checked')) {
                setMode('individual');
            }
        });
        $radioCor.on('change', () => {
            if ($radioCor.is(':checked')) {
                setMode('corporate');
            }
        });
        
        // Initialize with individual mode
        setMode('individual');
    },

    _saveSellerInfo: function () {
        const self = this;
        
        // Get seller type (individual or corporate)
        const sellerType = $('input[name="userType"]:checked').val();
        
        // Collect form data based on seller type using field system
        let formData = {
            seller_type: sellerType,
        };
        
        if (sellerType === 'corporate') {
            // Corporate fields using field system
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
            // Individual fields using field system
            formData = {
                ...formData,
                seller_name: this.seller.input.name.$.val(),
                seller_email: this.seller.input.email_individual.$.val(),
                seller_phone: this.seller.input.phone_individual.$.val(),
                seller_tc_number: this.seller.input.tc.$.val(),
                seller_birthdate: this.seller.input.birthdate.$.val(),
                seller_iban: this.seller.input.iban_individual.$.val(),
                seller_iban_name: this.seller.input.iban_name_individual.$.val(),
            };
        }
        
        // Make AJAX request to save seller info
        return this._rpc({
            route: '/my/seller/save',
            params: formData,
        }).then((result) => {
            // Store the seller partner_id for later use in product creation
            if (result.success && result.partner_id) {
                self.wizard.sellerId = result.partner_id;
                console.log('Seller saved with ID:', result.partner_id);
            }
            return result;
        });
    },

    // Save product information for both edit and new mode
    _saveProductInfo: function () {
        const self = this;
        
        // Check if we're in edit mode
        const isEditMode = this.wizard && this.wizard.editMode;
        const editingAdId = this.wizard && this.wizard.editingAdId;
        
        // Helper function to safely parse integer IDs
        const parseIntSafe = (value) => {
            const parsed = parseInt(value, 10);
            return isNaN(parsed) ? null : parsed;
        };
        
        // Collect product form data using field system
        const productData = {
            name: this.escrow.input.name.$.val(),
            categ_id: parseIntSafe(this.escrow.input.category.$.val()),
            price: this._parseTurkishPrice(this.escrow.input.price.$.val()),
            description: this.escrow.input.desc.$.val(),
            // Vehicle information with proper ID parsing
            escrow_car_vin: this.escrow.input.vin.$.val(),
            escrow_car_plate: this.escrow.input.plate.$.val(),
            escrow_car_brand_id: parseIntSafe(this.escrow.input.brand.$.val()),
            escrow_car_model_id: parseIntSafe(this.escrow.input.model.$.val()),
            escrow_car_model_year: parseIntSafe(this.escrow.input.year.$.val()),
            // Image data would need to be handled separately
            image_1920: null // TODO: Handle image upload
        };
        
        if (isEditMode && editingAdId) {
            // Update existing ad
            productData.id = parseIntSafe(editingAdId);
            return this._rpc({
                route: '/my/ad/save',
                params: productData,
            });
        } else {
            // Create new ad - add owner_id if we have a saved seller ID
            if (this.wizard && this.wizard.sellerId) {
                productData.owner_id = parseIntSafe(this.wizard.sellerId);
            }
            
            return this._rpc({
                route: '/my/ad/save',
                params: productData,
            }).then((result) => {
                // Store the saved product ID for recipient info step
                if (result.success && result.id) {
                    self.wizard.savedProductId = result.id;
                }
                return result;
            });
        }
    },

    // VIN doğrulama fonksiyonu
    _isValidVinChecksum: function(vin) {
        const map = {
            A: 1, B: 2, C: 3, D: 4, E: 5,
            F: 6, G: 7, H: 8, J: 1, K: 2,
            L: 3, M: 4, N: 5, P: 7, R: 9,
            S: 2, T: 3, U: 4, V: 5, W: 6,
            X: 7, Y: 8, Z: 9,
            '1': 1, '2': 2, '3': 3, '4': 4,
            '5': 5, '6': 6, '7': 7, '8': 8,
            '9': 9, '0': 0,
        };

        const weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2];
        let sum = 0;

        for (let i = 0; i < vin.length; i++) {
            const c = vin[i];
            const val = map[c];
            if (val === undefined) return false;
            sum += val * weights[i];
        }

        const checkDigit = vin[8];
        const remainder = sum % 11;
        const expected = remainder === 10 ? 'X' : remainder.toString();

        return checkDigit === expected;
    },

    // Save recipient information
    _saveRecipientInfo: function() {
        const recipientType = $('input[name="recipientType"]:checked').val();
        
        const data = {
            customer_type: recipientType,
        };

        // Add product_id if we're editing an existing ad or have a saved product
        if (this.wizard && this.wizard.editingAdId) {
            data.product_id = this.wizard.editingAdId;
        } else if (this.wizard && this.wizard.savedProductId) {
            data.product_id = this.wizard.savedProductId;
        }

        if (recipientType === 'individual') {
            // Individual recipient data using field system
            data.customer_name_surname = this.recipient.input.name_surname.$.val();
            data.customer_identity = this.recipient.input.identity.$.val();
            data.customer_birthdate = this.recipient.input.birthdate.$.val();
            data.customer_phone = this.recipient.input.phone_individual.$.val();
            data.customer_email = this.recipient.input.email_individual.$.val();
            data.customer_address = this.recipient.input.address_individual.$.val();
        } else {
            // Corporate recipient data using field system
            data.customer_corporate_title = this.recipient.input.corporate_title.$.val();
            data.customer_tax_number = this.recipient.input.tax_number.$.val();
            data.customer_tax_office = this.recipient.input.tax_office.$.val();
            data.customer_person = this.recipient.input.person.$.val();
            data.customer_phone = this.recipient.input.phone_corporate.$.val();
            data.customer_email = this.recipient.input.email_corporate.$.val();
            data.customer_address = this.recipient.input.address_corporate.$.val();
        }

        return this._rpc({
            route: '/my/customer/save',
            params: data,
        });
    },

    // IBAN doğrulama fonksiyonu
    _checkIban: function(iban, vat) {
        const self = this;
        
        if (!iban) {
            return Promise.resolve({
                success: false,
                message: 'IBAN gereklidir'
            });
        }
        
        return this._rpc({
            route: '/my/iban/check',
            params: {
                iban: iban,
                vat: vat || ''
            },
        });
    },

    // Recipient Info Form Initialization
    _initializeRecipientInfoForm: function() {
        const self = this;
        const $form = $('#recipientInfo');
        
        if (!$form.length) return;
        
        // Bind recipient type toggle
        this._bindRecipientToggle();
        
        // Initialize field validations
        this._bindRecipientValidations();
        
        // Auto uppercase for corporate title
        $form.find('#recipient_corporate_title').on('input', function() {
            this.value = this.value.toUpperCase();
        });

        // Phone number formatting
        $form.find('#recipient_phone_individual, #recipient_phone_corporate').on('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 3 && value.length <= 6) {
                value = value.slice(0, 3) + ' ' + value.slice(3);
            } else if (value.length > 6) {
                value = value.slice(0, 3) + ' ' + value.slice(3, 6) + ' ' + value.slice(6, 10);
            }
            this.value = value;
        });

        // Date formatting for birthdate
        $form.find('#recipient_birthdate').on('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.slice(0, 2) + '/' + value.slice(2);
            }
            if (value.length >= 5) {
                value = value.slice(0, 5) + '/' + value.slice(5, 9);
            }
            this.value = value;
        });

        // Tax number formatting
        $form.find('#recipient_tax_number').on('input', function() {
            this.value = this.value.replace(/\D/g, '').slice(0, 10);
        });

        // TC Identity formatting
        $form.find('#recipient_identity').on('input', function() {
            this.value = this.value.replace(/\D/g, '').slice(0, 11);
        });
    },

    // Bind recipient type toggle (similar to seller toggle)
    _bindRecipientToggle: function() {
        const self = this;
        const $form = $('#recipientInfo');
        const $radioTab = $form.find('.radioTab');
        const $slider = $radioTab.find('.radioTab__slider');
        const $individual = $('#recipientIndividual');
        const $corporate = $('#recipientCorporate');
        
        function setRecipientMode(mode) {
            // Unbind existing events first
            $form.find('input[name="recipientType"]').off('change.recipientToggle');
            
            if (mode === 'individual') {
                $form.find('input[name="recipientType"][value="individual"]').prop('checked', true);
                $individual.show();
                $corporate.hide();
                $slider.css('transform', 'translateX(0)');
            } else {
                $form.find('input[name="recipientType"][value="corporate"]').prop('checked', true);
                $individual.hide();
                $corporate.show();
                $slider.css('transform', 'translateX(100%)');
            }
            
            // Re-bind events after state change
            $form.find('input[name="recipientType"]').on('change.recipientToggle', function() {
                if ($(this).is(':checked')) {
                    setRecipientMode($(this).val());
                }
            });
        }
        
        // Initialize with individual mode
        setRecipientMode('individual');
    },

    // Recipient form validations
    _bindRecipientValidations: function() {
        const $form = $('#recipientInfo');
        
        if (!$form.length) return;
        
        const self = this;
        
        // Real-time validation binding
        $form.find('input, textarea').on('blur', function() {
            self._validateRecipientField($(this));
        });
    },

    // Validate individual recipient field
    _validateRecipientField: function($field) {
        const fieldName = $field.attr('name');
        const value = $field.val().trim();
        let isValid = true;
        let errorMessage = '';

        // Clear previous error
        $field.removeClass('is-invalid -error just-validate-error-field');
        $field.next('.form__error-label').remove();

        // Get current recipient type
        const recipientType = $('input[name="recipientType"]:checked').val();
        const isFieldVisible = $field.closest('#recipient' + (recipientType === 'individual' ? 'Individual' : 'Corporate')).is(':visible');
        
        if (!isFieldVisible) return true; // Skip validation for hidden fields

        switch (fieldName) {
            case 'recipient_name_surname':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Ad Soyad zorunludur';
                } else if (value.length < 2) {
                    isValid = false;
                    errorMessage = 'En az 2 karakter girin';
                }
                break;
                
            case 'recipient_identity':
                if (!value) {
                    isValid = false;
                    errorMessage = 'T.C. Kimlik Numarası zorunludur';
                } else if (!/^[1-9][0-9]{10}$/.test(value)) {
                    isValid = false;
                    errorMessage = '11 haneli geçerli T.C. No girin';
                }
                break;
                
            case 'recipient_birthdate':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Doğum tarihi zorunludur';
                } else if (!/^\d{2}\/\d{2}\/\d{4}$/.test(value)) {
                    isValid = false;
                    errorMessage = 'GG/AA/YYYY formatında girin';
                }
                break;
                
            case 'recipient_phone':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Telefon zorunludur';
                } else if (!/^[0-9\s]{10,15}$/.test(value)) {
                    isValid = false;
                    errorMessage = 'Geçerli bir telefon giriniz';
                }
                break;
                
            case 'recipient_email':
                if (!value) {
                    isValid = false;
                    errorMessage = 'E-posta zorunludur';
                } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                    isValid = false;
                    errorMessage = 'Geçerli bir e-posta giriniz';
                }
                break;
                
            case 'recipient_address':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Adres zorunludur';
                } else if (value.length < 10) {
                    isValid = false;
                    errorMessage = 'Adres çok kısa (en az 10 karakter)';
                }
                break;
                
            case 'recipient_corporate_title':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Firma unvanı zorunludur';
                }
                break;
                
            case 'recipient_tax_number':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Vergi numarası zorunludur';
                } else if (!/^[0-9]{10}$/.test(value)) {
                    isValid = false;
                    errorMessage = '10 haneli geçerli vergi no girin';
                }
                break;
                
            case 'recipient_tax_office':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Vergi dairesi zorunludur';
                } else if (value.length < 2) {
                    isValid = false;
                    errorMessage = 'En az 2 karakter girin';
                }
                break;
                
            case 'recipient_person':
                if (!value) {
                    isValid = false;
                    errorMessage = 'Yetkili kişi adı zorunludur';
                }
                break;
        }

        if (!isValid) {
            $field.addClass('is-invalid -error just-validate-error-field');
            $field.after(`<div class="form__error-label text-danger small mt-1">${errorMessage}</div>`);
        }

        return isValid;
    },

    // Validate entire recipient info step
    _validateRecipientInfo: function() {
        const self = this;
        const $form = $('#recipientInfo');
        let isValid = true;

        if (!$form.length) return true;

        // Get current recipient type
        const recipientType = $('input[name="recipientType"]:checked').val();
        
        // Clear all previous errors
        $form.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $form.find('.form__error-label').remove();

        // Get fields to validate based on type
        let fieldsToValidate;
        if (recipientType === 'individual') {
            fieldsToValidate = [
                '#recipient_name_surname',
                '#recipient_identity', 
                '#recipient_birthdate',
                '#recipient_phone_individual',
                '#recipient_email_individual',
                '#recipient_address_individual'
            ];
        } else {
            fieldsToValidate = [
                '#recipient_corporate_title',
                '#recipient_tax_number',
                '#recipient_tax_office',
                '#recipient_address_corporate',
                '#recipient_person',
                '#recipient_phone_corporate',
                '#recipient_email_corporate'
            ];
        }

        // Validate each field
        fieldsToValidate.forEach(function(selector) {
            const $field = $form.find(selector);
            if ($field.length) {
                const fieldValid = self._validateRecipientField($field);
                if (!fieldValid) {
                    isValid = false;
                }
            }
        });

        return isValid;
    },

});
