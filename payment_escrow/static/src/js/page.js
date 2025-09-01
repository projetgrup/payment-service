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
            }
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
        this.partner = new fields.integer({
            default: 0,
        });
        this.seller = {
            wizard: new fields.element(),
            button: {
                close: new fields.element({ events: [['click', this._onClickWizardClose]] }),
            },
            input: {
                name: new fields.string(),
                tc: new fields.string(),
                phone_individual: new fields.string(),
                email_individual: new fields.string(),
                address_individual: new fields.string(),
                iban_individual: new fields.string(),
                iban_name_individual: new fields.string(),
                corporate_title: new fields.string(),
                tax_number: new fields.string(),
                tax_office: new fields.string(),
                corporate_person: new fields.string(),
                phone_corporate: new fields.string(),
                email_corporate: new fields.string(),
                address_corporate: new fields.string(),
                iban_corporate: new fields.string(),
                iban_name_corporate: new fields.string(),
            }
        };
        this.customer = {
            input: {
                name_surname: new fields.string(),
                identity: new fields.string(),
                phone_individual: new fields.string(),
                email_individual: new fields.string(),
                address_individual: new fields.string(),
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
                }),
                name: new fields.string(),
                categ: new fields.selection(),
                price: new fields.float({
                    mask: payloxPage.prototype._maskAmount.bind(this),
                    default: 0,
                    events: [
                        ['update', this._onUpdateAmount],
                    ],
                }),
                id: new fields.integer(),
                category: new fields.selection(),
                brand: new fields.selection(),
                model: new fields.selection(),
                year: new fields.selection(),
                vin: new fields.string(),
                plate: new fields.string(),
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
                })
            },
            amount: {
                previous: new fields.element(),
                remaining: new fields.element(),
                total: new fields.element()
            },
            transaction: {
                reference: new fields.element()
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
            this._setInitialState();
            this._bindWizardValidation();
            this._bindWizardToggle();
            this._bindWizardSteps();
            this._bindImageUpload();
            this._checkStep5Parameter();
            framework.hideLoading();
        });
    },

    _setInitialState: function() {
        const $escrowItem = $('.escrow-ad-list-item[data-id], .escrow-item[data-id]').first();
        if ($escrowItem.length) {
            this.state.id = parseInt($escrowItem.data('id'), 10);
            return;
        }
    },
    
    _onUpdateAmount: function () {
        this.amount._.updateValue();
        this.amount.$.data('value', this.amount.value);
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

    _bindImageUpload: function() {
        const self = this;
        
        $(document).on('change', '#wizard_file_input', function(e) {
            const files = e.target.files;
            if (files && files.length > 0) {
                const firstFile = files[0];
                // Clear any previous preview to avoid duplicates
                self._clearImagePreview();
                self._setProductImage(firstFile);
            } else {
                // No selection or cleared; restore dashed area content
                self._clearImagePreview();
            }
        });
    },

    _setProductImage: function(file) {
        if (!file || !file.type.startsWith('image/')) {
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            if (this.ad && this.ad.input && this.ad.input.img) {
                this.ad.input.img.value = e.target.result;
            }
            this._showImagePreview(e.target.result);
        };
        reader.readAsDataURL(file);
    },

    _showImagePreview: function(imageSrc) {
        // Render the selected image inside the dashed upload label itself
        const $label = $('label[for="wizard_file_input"]');
        if (!$label.length) return;

        // Hide default icon/text within the label
        $label.find('svg, span, #wizard_num_of_files').addClass('d-none');

        // Create or update the preview image element
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

        // Remove any legacy small preview if present
        $('#image-preview').remove();
    },

    _clearImagePreview: function() {
        const $label = $('label[for="wizard_file_input"]');
        if ($label.length) {
            $label.find('img#wizard_image_preview').remove();
            $label.find('svg, span, #wizard_num_of_files').removeClass('d-none');
        }
        // Also remove any legacy preview container
        $('#image-preview').remove();
    },

    _openSellerEditForCard: function(id, section) {
        this._closeSidebar();
        if (section === 'seller') {
            this._navigateToStep(1);
        } else if (section === 'vehicle') {
            this._navigateToStep(2);
        }
    },

    _parseAds: function () {
        $('[field="ad.item"][data-value]').each((i, e) => {
            const $this = $(e);
            const categ = $this.find('.escrow-ad-item-categ');
            this.values.ads[e.dataset.id] = {
                id: $this.data('id'),
                img: $this.find('.escrow-ad-item-image img').attr('src'),
                name: $this.find('.escrow-ad-item-name').text().trim(),
                categ: categ.data('id'),
                price: $this.find('.escrow-ad-item-price').data('value'),
                state: $this.find('.escrow-ad-item-state').html().trim(),
                owner_id: $this.data('owner-id'),
                customer_id: $this.data('customer-id'),
                vin: $this.data('vin'),
                plate: $this.data('plate'),
                brand_id: $this.data('brand-id'),
                brand_name: $this.data('brand-name'),
                model_id: $this.data('model-id'),
                model_name: $this.data('model-name'),
                year: $this.data('model-year'),
                item_id: $this.data('item-id'),
                amount: $this.data('item-amount'),
                residual_amount: $this.data('item-residual-amount'),
                paid_amount: $this.data('item-paid-amount'),
            };
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
            const $errorDiv = $('<div class="form__error-label just-validate-error-label">Amount is required</div>');
            $group.append($errorDiv);
            return false;
        }

        const raw = parseInt(getRawValue(val), 10);
        if (isNaN(raw) || raw <= 0) {
            $input.addClass('is-invalid -error just-validate-error-field');
            const $errorDiv = $('<div class="form__error-label just-validate-error-label">Enter an amount greater than 0</div>');
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
        bindValidCheck('#wizard_year', (v) => { const year = parseInt(v, 10);return !isNaN(year) && year > 1900 && year <= new Date().getFullYear();});
    },

    _updateAds: function (value) {
        if (this.state.id) {
            Object.assign(this.values.ads[value.id], {
                img: value.img,
                name: value.name,
                categ: value.categ,
                price: value.price,
            });

            const $items = this.ad.item.$.filter(`[data-id=${value.id}]`);
            if ($items.length) {
                $items.find('[name=name]').text(value.name);
                $items.find('[name=categ]').text(value.categ[1]).data('id', value.categ[0]);
                $items.find('[name=price]').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
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
                state: '-',
            };

            const $items = this.ad.item.$.filter(`[data-id=${value.id}]`);
            if ($items.length) {
                $items.find('[name=name]').text(value.name);
                $items.find('[name=categ]').text(value.categ[1]).data('id', value.categ[0]);
                $items.find('[name=price]').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
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
        this._openWizard();
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
                    self.values.ads[adId].seller_iban = self._formatIban(bankAccount.acc_number) || 'Not Specified';
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
        if (adData.price) this.ad.input.price.$.val(format.currency(adData.price, this.currency.decimal));
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
        if (adData.model_id) {
            this.ad.input.model.$.val(adData.model_id);
            this.ad.input.model.$.trigger('change');
        }
        if (adData.year) {
            this.ad.input.year.$.val(adData.year);
        }

        if (adData.img) {
            let src = adData.img;
            if (typeof src === 'string' && !src.startsWith('data:image/')) {
                src = 'data:image/png;base64,' + src;
            }
            if (this.ad && this.ad.input && this.ad.input.img) {
                this.ad.input.img.value = src;
            }
            this._showImagePreview(src);
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


    _onClickButtonSave: function (ev) {
        framework.showLoading();
        this._saveAdData()
            .then((result) => {
                this._updateAds({
                    id: result.id,
                    img: this.ad.input.img.value,
                    name: this.ad.input.name.value || '',
                    categ: [this.ad.input.categ.value, this.ad.input.categ.text],
                    price: this.ad.input.price.value,
                });
                this._activateView('list');
                this.displayNotification({
                    type: 'success',
                    title: _t('Success'),
                    message: this.state.id ? _t('Ad has been updated.') : _t('Ad has been saved.'),
                });
            })
            .catch((error) => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: error.message || _t('An error occurred. Please contact with your system administrator.'),
                });
            })
            .finally(() => {
                framework.hideLoading();
            });
    },

    _parsePrice: function(priceStr) {
        if (!priceStr) return 0;
        const str = String(priceStr);
        const cleaned = str.replace(/\./g, '').replace(',', '.');
        console.log(cleaned)
        const parsed = parseFloat(cleaned);
        console.log(parsed)
        return isNaN(parsed) ? 0 : parsed;
    },

    _saveAdData: function(useWizardForm = false) {
        const isEditMode = this.state.id > 0;
        let params;
        if (useWizardForm) {
            params = {
                id: isEditMode ? this.state.id : null,
                categ_id: parseInt(this.ad.input.category.$.val(), 10) || null,
                price: this._parsePrice($('#wizard_price').val()),
                escrow_car_vin: this.ad.input.vin.$.val(),
                escrow_car_plate: this.ad.input.plate.$.val(),
                escrow_car_brand_id: parseInt(this.ad.input.brand.$.val(), 10) || null,
                escrow_car_model_id: parseInt(this.ad.input.model.$.val(), 10) || null,
                escrow_car_model_year: parseInt(this.ad.input.year.$.val(), 10) || null,
                image_1920: this.ad.input.img.value || null
            };
            
            if (this.wizard && this.wizard.sellerId) {
                params.escrow_owner_id = this.wizard.sellerId;
            }
        } else {
            params = {
                id: this.state.id,
                categ: [this.ad.input.categ.value, this.ad.input.categ.text],
                price: this._parsePrice(this.ad.input.price.value),
                img: this.ad.input.img.value,
            };
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
        this._openWizard(id);
    },

    _onClickAd: function (ev) {
        this._onClickButtonSidebarToggle({ currentTarget: { dataset: { value: 'items'}}});

        const id = ev?.currentTarget?.dataset?.id;
        this.state.id = id ? parseInt(id, 10) : 0;
        const value = this.values.ads[id];
        if (value && value.owner_id && !value.seller_name) {
            this._loadSellerInfoForSidebar(id, value.owner_id);
        }
        const $item = $('.escrow-ad-sidebar-items');
        if ($item.length) {
            $item.find('.escrow-ad-item-name').text(value.name);
            $item.find('.escrow-ad-item-categ').text(value.categ);
            $item.find('.seller-name').text(value.seller_name || 'Not specified');
            $item.find('.seller-tc').text(value.seller_tc || 'Not specified');
            $item.find('.seller-iban').text(value.seller_iban || 'Not specified');
            
            const brandModel = value.brand && value.model ? `${value.brand} / ${value.model}` : 'Not specified';
            $item.find('.escrow-ad-item-brand-model').text(brandModel);
            $item.find('.escrow-ad-item-year').text(value.year || 'Not specified');
            $item.find('.escrow-ad-item-plate').text(value.plate || 'Not specified');
            $item.find('.escrow-ad-item-vin').text(value.vin || 'Not specified');

            $item.find('.escrow-ad-item-price').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
            $item.find('.escrow-ad-item-state').html(value.state);
            $item.find('.escrow-ad-button-edit').data('id', id);
            $item.find('.escrow-ad-button-delete').data('id', id);
            $item.find('.escrow-ad-button-continue').data('id', id);
            if (value.residual_amount !== undefined) {
                $('#remainingBalance').text(format.currency(value.residual_amount, this.currency.position, this.currency.symbol, this.currency.decimal));
            }
        } else {
            $item.find('.seller-name, .seller-tc, .seller-iban').text('Not specified');
            $item.find('.vehicle-brand-model, .vehicle-year, .vehicle-plate, .vehicle-vin').text('Not specified');
            $item.find('.escrow-ad-item-price').text('');
            $item.find('.escrow-ad-item-state').html('');
            $item.find('.escrow-ad-item-name').text(_t('No ad found'));
            $item.find('.escrow-ad-item-categ').text('');
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

            if (adData.model_id && this.ad.input.model.$.find('option[value="' + adData.model_id + '"]').length) {
                this.ad.input.model.$.val(adData.model_id);
            } else if (adData.model_name) {
                const $modelOpt = this.ad.input.model.$.find('option').filter((i, e) => $(e).text().trim() === adData.model_name);
                if ($modelOpt.length) {
                    this.ad.input.model.$.val($modelOpt.val());
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
            setTimeout(() => this.ad.input.img.value = ad.img, 1000);

        } else {
            this.state.id = 0;
            this.ad.input.name.value = '';
            this.ad.input.categ.value = '';
            this.ad.input.price.value = format.float(0);
            this.ad.input.img.reset();
        }
    },

    _openWizard: function (id) {
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
        if (!id) {
            const $categorySelect = $wiz.find('#wizard_category');
            const $firstOption = $categorySelect.find('option[value!=""]').first();
            if ($firstOption.length) {
                $categorySelect.val($firstOption.val());
                $categorySelect.trigger('change');
            }
        }
        
        this._updateStepStates();
    },

    _onClickWizardClose: function () {
        this.seller.wizard.$.fadeOut(200, () => {
            this.seller.wizard.$.addClass('d-none');
            $('.escrow-ad-read').removeClass('d-none').fadeIn(200);
        });
    },

    _saveSellerData: function() {
        const self = this;
        
        return new Promise((resolve, reject) => {
            const sellerData = this._getSellerFormData();
            
            this._rpc({
                route: '/my/seller/save',
                params: sellerData
            }).then((sellerResult) => {
                if (!sellerResult.success) {
                    reject(new Error(sellerResult.message || 'Seller registration error'));
                    return;
                }
                self.wizard.sellerId = sellerResult.partner_id;
                
                return self._saveAdData(true);
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
            sellerData.seller_phone = this.seller.input.phone_individual.$.val();
            sellerData.seller_email = this.seller.input.email_individual.$.val();
            sellerData.seller_iban = this.seller.input.iban_individual.$.val();
            sellerData.seller_iban_name = this.seller.input.iban_name_individual.$.val();
        }
        
        return sellerData;
    },

    _loadAds: function() {
        window.location.reload();
    },

    _bindWizardValidation: function () {
        const self = this;
        const $wiz = $('.escrow-wizard');
        if (!$wiz.length) return;

        const isValidIBAN = (iban) => {
            const cleanIban = iban.replace(/\s/g, '').toUpperCase();
            
            if (!/^TR\d{24}$/.test(cleanIban)) {
                return false;
            }
            
            const rearranged = cleanIban.substring(4) + cleanIban.substring(0, 4);
            
            let numericString = '';
            for (let i = 0; i < rearranged.length; i++) {
                const char = rearranged[i];
                if (char >= 'A' && char <= 'Z') {
                    numericString += (char.charCodeAt(0) - 65 + 10).toString();
                } else {
                    numericString += char;
                }
            }
            
            let remainder = 0;
            for (let i = 0; i < numericString.length; i++) {
                remainder = (remainder * 10 + parseInt(numericString[i])) % 97;
            }
            
            return remainder === 1;
        };

        const isValidTCKN = (tckn) => {
            const cleanTckn = tckn.replace(/\D/g, '');
            if (cleanTckn.length !== 11) {
                return false;
            }
            
            const digits = cleanTckn.split('').map(Number);
            
            if (digits[0] === 0) {
                return false;
            }
            
            const oddSum = digits[0] + digits[2] + digits[4] + digits[6] + digits[8];
            const evenSum = digits[1] + digits[3] + digits[5] + digits[7];
            
            const checkDigit10 = ((oddSum * 7) - evenSum) % 10;
            const checkDigit11 = (digits.slice(0, 10).reduce((a, b) => a + b, 0)) % 10;
            
            return digits[9] === checkDigit10 && digits[10] === checkDigit11;
        };

        const isValidEmail = (email) => {
            const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
            
            if (!emailRegex.test(email)) {
                return false;
            }

            const parts = email.split('@');
            if (parts.length !== 2) return false;
            
            const [localPart, domainPart] = parts;
            
            if (localPart.length > 64 || localPart.length === 0) return false;
            if (localPart.startsWith('.') || localPart.endsWith('.')) return false;
            if (localPart.includes('..')) return false;
            
            if (domainPart.length > 253 || domainPart.length === 0) return false;
            if (domainPart.startsWith('-') || domainPart.endsWith('-')) return false;
            if (domainPart.startsWith('.') || domainPart.endsWith('.')) return false;
            
            const domainParts = domainPart.split('.');
            const tld = domainParts[domainParts.length - 1];
            if (tld.length < 2) return false;
            
            const invalidDomains = ['tempmail.com', '10minutemail.com', 'mailinator.com', 'guerrillamail.com'];
            if (invalidDomains.some(domain => domainPart.toLowerCase().includes(domain))) {
                return false;
            }
            
            return true;
        };

        this.validationErrors = {};
        this.validationRules = {
            '#namesurname': [
                { rule: 'required', errorMessage: 'Full Name is required' }
            ],
            '#wizard_tckn': [
                { rule: 'required', errorMessage: 'T.C. Identity No required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidTCKN(val),
                    errorMessage: '11 digit valid T.C. No required'
                }
            ],
            '#email_individual': [
                { rule: 'required', errorMessage: 'E-mail is required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidEmail(val),
                    errorMessage: 'Please enter a valid e-mail address (format, domain, and TLD check)'
                }
            ],
            '#phone_individual': [
                { rule: 'required', errorMessage: 'Phone number is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9\s]{10,15}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Please enter a valid phone number'
                }
            ],
            '#wizard_iban': [
                { rule: 'required', errorMessage: 'IBAN is required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidIBAN(val),
                    errorMessage: 'Please enter a valid TR IBAN (mod-97 check)'
                }
            ],
            '#ibanaccountname_individual': [
                { rule: 'required', errorMessage: 'Account name is required' }
            ],
            '#corporate_title': [
                { rule: 'required', errorMessage: 'Company title is required' }
            ],
            '#wizard_tax': [
                { rule: 'required', errorMessage: 'Tax number is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9]{10}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Please enter a valid 10-digit tax number'
                }
            ],
            '#corporate_person': [
                { rule: 'required', errorMessage: 'Authorized person name is required' }
            ],
            '#email_corporate': [
                { rule: 'required', errorMessage: 'E-mail is required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidEmail(val),
                    errorMessage: 'Please enter a valid e-mail address (format, domain, and TLD check)'
                }
            ],
            '#phone_corporate': [
                { rule: 'required', errorMessage: 'Phone number is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9\s]{10,15}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Please enter a valid phone number'
                }
            ],
            '#wizard_iban_corp': [
                { rule: 'required', errorMessage: 'IBAN is required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidIBAN(val),
                    errorMessage: 'Please enter a valid TR IBAN (mod-97 check)'
                }
            ],
            '#ibanaccountname_corporate': [
                { rule: 'required', errorMessage: 'Account name is required' }
            ],
            '#wizard_category': [
                { rule: 'required', errorMessage: 'Sales category is required' },
                {
                    rule: 'custom',
                    validator: (val) => val !== '' && val !== '0',
                    errorMessage: 'Please select a sales category'
                }
            ],
            // '#wizard_price': [
            //     { rule: 'required', errorMessage: 'Sales price is required' },
            //     {
            //         rule: 'custom',
            //         validator: (val) => {
            //             const cleanVal = val.replace(/[^\d.,]/g, '');
            //             return /^\d+([.,]\d{1,3})*([,]\d{2})?$/.test(cleanVal) && cleanVal.length > 0;
            //         },
            //         errorMessage: 'Please enter a valid price (e.g., 1.000.000,00)'
            //     },
            //     {
            //         rule: 'custom',
            //         validator: (val) => {
            //             const numericValue = parseFloat(val.replace(/[^\d,]/g, '').replace(',', '.')) || 0;
            //             return numericValue > 0;
            //         },
            //         errorMessage: 'Price must be greater than zero'
            //     }
            // ],
            '#wizard_vin': [
                { rule: 'required', errorMessage: 'VIN is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^[A-HJ-NPR-Z0-9]{17}$/.test(val.toUpperCase()),
                    errorMessage: 'Please enter a valid 17-character VIN'
                },
                {
                    rule: 'custom',
                    validator: (val) => self._isValidVinChecksum(val.toUpperCase()),
                    errorMessage: 'Invalid VIN (checksum is incorrect)'
                }
            ],
            '#wizard_plate': [
                { rule: 'required', errorMessage: 'License plate is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^(0[1-9]|[1-7][0-9]|8[01])\s?[A-Z]{1,3}\s?[0-9]{1,4}$/.test(val),
                    errorMessage: 'Please enter a valid license plate (e.g., 34 ABC 123)'
                }
            ],
            '#wizard_brand': [
                { rule: 'required', errorMessage: 'Brand is required' },
                {
                    rule: 'custom',
                    validator: (val) => val !== '' && val !== '0',
                    errorMessage: 'Please select a brand'
                }
            ],
            '#wizard_model': [
                { rule: 'required', errorMessage: 'Model is required' },
                {
                    rule: 'custom',
                    validator: (val) => val !== '' && val !== '0',
                    errorMessage: 'Please select a model'
                }
            ],
            '#wizard_year': [
                { rule: 'required', errorMessage: 'Year is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^\d{4}$/.test(val),
                    errorMessage: 'Year must be a number'
                },
                {
                    rule: 'custom',
                    validator: (val) => {
                        const year = parseInt(val);
                        return year >= 1950 && year <= new Date().getFullYear();
                    },
                    errorMessage: 'Please enter a valid year'
                }
            ],
            '#wizard_file_input': [
                {
                    rule: 'custom',
                    validator: () => {
                        const input = $wiz.find('#wizard_file_input')[0];
                        const hasNewFiles = input && input.files && input.files.length > 0;
                        const hasExistingImage = self.ad.input.img.value && self.ad.input.img.value.length > 0;
                        const isEditMode = self.wizard && self.wizard.editMode;
                        return hasNewFiles || (isEditMode && hasExistingImage);
                    },
                    errorMessage: 'At least one file must be selected'
                }
            ],
            '#recipient_name_surname': [
                { rule: 'required', errorMessage: 'Name Surname is required' },
                {
                    rule: 'custom',
                    validator: (val) => val.length >= 2,
                    errorMessage: 'Please enter at least 2 characters'
                }
            ],
            '#recipient_identity': [
                { rule: 'required', errorMessage: 'T.C. Identity No is required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidTCKN(val),
                    errorMessage: '11 digit valid T.C. No required'
                }
            ],
            '#recipient_phone_individual': [
                { rule: 'required', errorMessage: 'Phone is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9\s]{10,15}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Please enter a valid phone number'
                }
            ],
            '#recipient_email_individual': [
                { rule: 'required', errorMessage: 'E-mail is required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidEmail(val),
                    errorMessage: 'Please enter a valid e-mail address (format, domain, and TLD check)'
                }
            ],
            '#recipient_address_individual': [
                { rule: 'required', errorMessage: 'Address is required' },
                {
                    rule: 'custom',
                    validator: (val) => val.length >= 10,
                    errorMessage: 'Address is too short (at least 10 characters)'
                }
            ],
            '#recipient_corporate_title': [
                { rule: 'required', errorMessage: 'Company title is required' }
            ],
            '#recipient_tax_number': [
                { rule: 'required', errorMessage: 'Tax number is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9]{10}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Please enter a valid 10-digit tax number'
                }
            ],
            '#recipient_tax_office': [
                { rule: 'required', errorMessage: 'Tax office is required' },
                {
                    rule: 'custom',
                    validator: (val) => val.length >= 2,
                    errorMessage: 'Please enter at least 2 characters'
                }
            ],
            '#recipient_person': [
                { rule: 'required', errorMessage: 'Authorized person name is required' }
            ],
            '#recipient_phone_corporate': [
                { rule: 'required', errorMessage: 'Phone is required' },
                {
                    rule: 'custom',
                    validator: (val) => /^[0-9\s]{10,15}$/.test(val.replace(/\D/g, '')),
                    errorMessage: 'Please enter a valid phone number'
                }
            ],
            '#recipient_email_corporate': [
                { rule: 'required', errorMessage: 'E-mail is required' },
                {
                    rule: 'custom',
                    validator: (val) => isValidEmail(val),
                    errorMessage: 'Please enter a valid e-mail address (format, domain, and TLD check)'
                }
            ],
            '#recipient_address_corporate': [
                { rule: 'required', errorMessage: 'Address is required' },
                {
                    rule: 'custom',
                    validator: (val) => val.length >= 10,
                    errorMessage: 'Address is too short (at least 10 characters)'
                }
            ]
        };

        const validateField = (selector, showError = true) => {
            const $field = $wiz.find(selector);
            if (!$field.length) return true;

            const value = $field.val() || '';
            const rules = this.validationRules[selector] || [];
            
            if (selector.includes('#recipient_')) {
                const recipientType = $('input[name="userType"]:checked').val();
                const isIndividualField = selector.includes('_individual') || 
                    ['#recipient_name_surname', '#recipient_identity'].includes(selector);
                const isCorporateField = selector.includes('_corporate') || 
                    ['#recipient_corporate_title', '#recipient_tax_number', '#recipient_tax_office', '#recipient_person'].includes(selector);
                
                if ((recipientType === 'individual' && isCorporateField) || 
                    (recipientType === 'corporate' && isIndividualField)) {
                    return true;
                }
            }
            
            $field.removeClass('is-invalid -error just-validate-error-field -success');
            const $group = $field.closest('.form__group');
            $group.find('.form__error-label, .just-validate-error-label').remove();
            $group.find('.state-check').addClass('d-none');
            $group.find('.form__error').addClass('d-none');

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
                                             selector === '#wizard_tckn' || selector === '#wizard_iban' || 
                                             selector === '#ibanaccountname_individual';
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

        const emailFields = ['#email_individual', '#email_corporate', '#recipient_email_individual', '#recipient_email_corporate'];
        emailFields.forEach(selector => {
            const $emailField = $wiz.find(selector);
            if ($emailField.length) {
                $emailField.on('blur', function() {
                    const email = $(this).val().trim();
                    const $field = $(this);
                    const $group = $field.closest('.form__group');
                    
                    $group.find('.email-verification-status').remove();
                    
                    if (email && email.includes('@')) {
                        const isValid = isValidEmail(email);
                        
                        if (isValid) {
                            $group.append('<div class="email-verification-status text-success small mt-1">✅ E-mail format corrected</div>');
                        } else {
                            $group.append('<div class="email-verification-status text-danger small mt-1">❌ E-mail format invalid</div>');
                        }
                    }
                });
                
                $emailField.on('input', function() {
                    $(this).closest('.form__group').find('.email-verification-status').remove();
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
                $counter.text(`${files.length} File Selected`);
                $filesList.empty();
                
                Array.from(files).forEach((file, index) => {
                    $filesList.append(`<li>${file.name}</li>`);
                });
                const first = files[0];
                if (first && first.type && first.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const $label = $('label[for="wizard_file_input"]');
                        $label.find('svg, span, #wizard_num_of_files').addClass('d-none');
                        let $img = $label.find('img#wizard_image_preview');
                        if (!$img.length) {
                            $img = $('<img id="wizard_image_preview" alt="License Photo"/>')
                                .css({ width: '100%', height: 'auto', display: 'block', marginTop: '8px', objectFit: 'contain' });
                            $label.append($img);
                        }
                        $img.attr('src', e.target.result);
                    };
                    reader.readAsDataURL(first);
                }
            } else {
                $counter.text('No Files Selected');
                $filesList.empty();
                const $label = $('label[for="wizard_file_input"]');
                $label.find('img#wizard_image_preview').remove();
                $label.find('svg, span, #wizard_num_of_files').removeClass('d-none');
            }
            
            const selector = '#wizard_file_input';
            if (self.validationRules[selector]) {
                setTimeout(() => validateField(selector), 100);
            }
        });

        $wiz.find('#recipient_corporate_title').on('input', function() {
            this.value = this.value.toUpperCase();
        });

        $wiz.find('#recipient_phone_individual, #recipient_phone_corporate').on('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 3 && value.length <= 6) {
                value = value.slice(0, 3) + ' ' + value.slice(3);
            } else if (value.length > 6) {
                value = value.slice(0, 3) + ' ' + value.slice(3, 6) + ' ' + value.slice(6, 10);
            }
            this.value = value;
        });

        $wiz.find('#phone_individual, #phone_corporate').on('input', function() {
            let value = this.value.replace(/\D/g, '');
            if (value.length > 3 && value.length <= 6) {
                value = value.slice(0, 3) + ' ' + value.slice(3);
            } else if (value.length > 6) {
                value = value.slice(0, 3) + ' ' + value.slice(3, 6) + ' ' + value.slice(6, 10);
            }
            this.value = value;
        });

        $wiz.find('#recipient_tax_number').on('input', function() {
            this.value = this.value.replace(/\D/g, '').slice(0, 10);
        });

        $wiz.find('#recipient_identity').on('input', function() {
            this.value = this.value.replace(/\D/g, '').slice(0, 11);
        });

        $wiz.find('#recipient_identity').on('change', function() {
            const identity = this.value.trim();
            if (identity.length === 11) {
                self._lookupCustomerByIdentity(identity, 'individual');
            }
        });

        $wiz.find('#recipient_tax_number').on('change', function() {
            const taxNumber = this.value.trim();
            if (taxNumber.length === 10) {
                self._lookupCustomerByIdentity(taxNumber, 'corporate');
            }
        });

        this.validateWizardStep1 = () => {
            const mode = this.getCurrentMode();
            let isValid = true;

            if (mode === 'individual') {
                const fields = ['#namesurname', '#wizard_tckn', '#email_individual', '#phone_individual', '#wizard_iban', '#ibanaccountname_individual'];
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
            const fields = ['#wizard_category', '#wizard_vin', '#wizard_plate', '#wizard_brand', '#wizard_model', '#wizard_year', '#wizard_file_input'];
            
            fields.forEach(selector => {
                if (!validateField(selector)) {
                    isValid = false;
                }
            });

            return isValid;
        };

        this.validateWizardStep3 = () => {
            let isValid = true;
            const recipientType = $('input[name="userType"]:checked').val();

            let fieldsToValidate;
            if (recipientType === 'individual') {
                fieldsToValidate = [
                    '#recipient_name_surname',
                    '#recipient_identity', 
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
            
            fieldsToValidate.forEach(selector => {
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
            const targetStep = parseInt($(this).data('step'));
            const current = self.wizard.currentStep;

            if (targetStep <= current) {
                self._navigateToStep(targetStep);
                return;
            }
            const $targetItem = $(`.steps__item:nth-child(${targetStep})`);
            if ($targetItem.hasClass('-completed')) {
                self._navigateToStep(targetStep);
                return;
            }
            if (targetStep === current + 1) {
                if (self._validateCurrentStep()) {
                    self._navigateToStep(targetStep);
                } else {
                    self.displayNotification({
                        type: 'warning',
                        title: 'Error',
                        message: 'Please fill in the current step before proceeding to the next step.',
                    });
                }
            }
        });

        $(document).on('click', '.steps__item:not(.-active)', function (ev) {
            ev.preventDefault();
            const $stepItem = $(this);
            const targetStep = $stepItem.index() + 1;
            const current = self.wizard.currentStep;

            if (targetStep <= current) {
                self._navigateToStep(targetStep);
                return;
            }

            if ($stepItem.hasClass('-completed')) {
                self._navigateToStep(targetStep);
                return;
            }
            if (targetStep === current + 1) {
                if (self._validateCurrentStep()) {
                    self._navigateToStep(targetStep);
                } else {
                    self.displayNotification({
                        type: 'warning',
                        title: 'Uyarı',
                        message: 'Please fill in the current step before proceeding to the next step.',
                    });
                }
            }
        });
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
        $('.escrow-ad-read').addClass('d-none');
        this.seller.wizard.$.removeClass('d-none');
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
        $('.wizard-step').addClass('d-none');
        $(`.wizard-step-${stepNumber}`).removeClass('d-none');
    },

    _handleStepSpecificActions: function(stepNumber, options, stateId) {
        switch(stepNumber) {
            case 1:
                this._initializeSellerInfoForm(stateId);
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
                this._showCompletionStep(stateId);
                break;
        }
    },

    _showCompletionStep: function() {
        this.displayNotification({
            type: 'success',
            title: 'Payment Completed',
            message: 'Your escrow payment has been completed successfully.',
            sticky: false
        });
    },

    _navigateToStep: function(stepNumber) {
        this._updatePaymentAmounts(this.state.item_id);
        this._onChangeStep(stepNumber, {});
    },

    _getItemDetails: function(itemId) {
        const data = this._updatePaymentAmounts(itemId);
        console.log(data);
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

    _nextStep: function () {
        const self = this;
        if (!self._validateCurrentStep()){
            self.displayNotification({ type: 'warning', title: 'Step Invalid', message: 'Please fill in all required fields.' });
            return;
        }
        if (this.wizard.currentStep === 1) {
            this._saveSellerInfo().then(function(result) {
                if (result.success) {
                    self.displayNotification({
                        type: 'success',
                        title: 'Success',
                        message: 'Seller information saved',
                    });
                    return self._startOtp(result.partner_id).then((otpRes) => {
                        if (otpRes && otpRes.success) {
                            self.wizard.otpId = otpRes.otp_id;
                            self._showOtpModal(otpRes.expires_in || 120);
                        } else if (otpRes && otpRes.is_otp_verified) {
                            self.displayNotification({ type: 'info', title: 'OTP', message: 'OTP has already been verified.' });
                            self._markStepCompleted(self.wizard.currentStep);
                            self._navigateToStep(self.wizard.currentStep + 1);
                        } else {
                            self.displayNotification({ type: 'warning', title: 'OTP', message: (otpRes && otpRes.message) || 'OTP could not be started' });
                        }
                        return result;
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
            return false;
        }

        if (this.wizard.currentStep === 2) {
            this._saveProductInfo().then(function(result) {
                if (result.success || result.id) {
                    if (result.id) {
                        self.wizard.savedProductId = result.id;
                        self.state.item_id = result.item_id;
                    }
                    
                    self._markStepCompleted(self.wizard.currentStep);
                    self._navigateToStep(self.wizard.currentStep + 1);

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
                            self._navigateToStep(self.wizard.currentStep + 1);
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

        if (this.wizard.currentStep < 5) {
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
                return this.validateWizardStep2();
            case 3:
                return this.validateWizardStep3();
            case 4:
                return this._validatePaymentInfo();
            default:
                return true;
        }
    },

    _validatePaymentInfo: function () {
        const $wiz = $('.escrow-wizard');
        let isValid = true;

        $wiz.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $wiz.find('.form__error-label, .just-validate-error-label').remove();

        const showError = ($field, message) => {
            $field.addClass('is-invalid -error just-validate-error-field');
            const $group = $field.closest('.form__group');
            const $errorDiv = $(`<div class="form__error-label just-validate-error-label">${message}</div>`);
            $group.append($errorDiv);
            isValid = false;
        };

        const $cardHolder = $wiz.find('#card_holder_name');
        if ($cardHolder.length) {
            const cardHolderValue = $cardHolder.val().trim();
            if (!cardHolderValue) {
                showError($cardHolder, 'Card holder name is required');
            } else if (cardHolderValue.length < 3) {
                showError($cardHolder, 'Card holder name must be at least 3 characters long');
            }
        }

        const $cardNumber = $wiz.find('#card_number');
        if ($cardNumber.length) {
            const cardNumberValue = $cardNumber.val().replace(/\D/g, '');
            if (!cardNumberValue) {
                showError($cardNumber, 'Card number is required');
            } else if (cardNumberValue.length < 16) {
                showError($cardNumber, 'Please enter a valid card number');
            }
        }
        const $cardExpiry = $wiz.find('#card_expiry');
        if ($cardExpiry.length) {
            const expiryValue = $cardExpiry.val().trim();
            if (!expiryValue) {
                showError($cardExpiry, 'Expiration date is required');
            } else if (!/^\d{2}\/\d{2}$/.test(expiryValue)) {
                showError($cardExpiry, 'Please enter in MM/YY format');
            }
        }
        const $cvv = $wiz.find('#cvv');
        if ($cvv.length) {
            const cvvValue = $cvv.val().replace(/\D/g, '');
            if (!cvvValue) {
                showError($cvv, 'Security code is required');
            } else if (cvvValue.length < 3) {
                showError($cvv, 'Security code must be at least 3 digits long');
            }
        }
        const paymentAmountValid = this._validatePartialPriceField();
        if (!paymentAmountValid) {
            isValid = false;
        }

        const $agreement = $wiz.find('#agreementChk');
        if ($agreement.length && !$agreement.is(':checked')) {
            const $agreementLabel = $agreement.closest('label');
            $agreementLabel.addClass('text-danger');
            $agreementLabel.after('<div class="form__error-label just-validate-error-label">You must accept the terms and conditions</div>');
            isValid = false;
        }

        return isValid;
    },

    _initializeSellerInfoForm: function (stateId) {
        this._setupFileUpload();
        this._bindWizardToggle();
        this._prefillSellerFromAd(this.values.ads[this.state.id]);
    },

    _initializeProductInfoForm: function (stateId) {
        this._setupFileUpload();
        this._getProductData();
        this._prefillProductFromAd(this.values.ads[this.state.id]);
    },

    _initializeCustomerInfoForm: function (stateId) {
        this._bindRecipientToggle();
    },

    _initializePaymentForm: function (stateId) {
        this._setupFileUpload();
        this._setupCreditCardInstallments(this.values.ads[stateId]);
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
                    model_id: product.ad.model_id,
                    model_name: product.ad.model_name,
                    year: product.ad.year,
                    item_id: product.ad.item_id,
                    amount: product.ad.amount,
                    residual_amount: product.ad.residual_amount,
                    paid_amount: product.ad.paid_amount,
                };
            }
        });
    },

    _setupCreditCardInstallments: function() {
        const $wiz = $('.escrow-wizard');
        const $cardNumber = $wiz.find('#card_number');
        const $cardExpiry = $wiz.find('#card_expiry');
        const $cvv = $wiz.find('#cvv');
        const $installmentContainer = $wiz.find('#installmentOptionsContainer');
        const $cardInfoNotice = $wiz.find('.card-info-notice');

        if (!$cardNumber.length || !$installmentContainer.length) return;
        
        const checkBINAndFetchInstallments = (cardNumber) => {
                if (cardNumber.length >= 6) {
                    $cardInfoNotice.addClass('d-none');
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
                $btnInd.toggleClass('btn-dark active', isInd).toggleClass('btn-outline-dark', !isInd);
                $btnCor.toggleClass('btn-outline-dark', isInd).toggleClass('btn-dark active', !isInd);
            }

            if ($slider.length) {
                $slider.css('transform', isInd ? 'translateX(0%)' : 'translateX(100%)');
            }
        }

        $btnInd.off('click.userTypeToggle');
        $btnCor.off('click.userTypeToggle');
        $radioInd.off('change.userTypeToggle');
        $radioCor.off('change.userTypeToggle');

        if ($btnInd.length) $btnInd.on('click.userTypeToggle', (e) => { e.preventDefault(); setMode('individual'); });
        if ($btnCor.length) $btnCor.on('click.userTypeToggle', (e) => { e.preventDefault(); setMode('corporate'); });
        if ($radioInd.length) $radioInd.on('change.userTypeToggle', () => { if ($radioInd.is(':checked')) setMode('individual'); });
        if ($radioCor.length) $radioCor.on('change.userTypeToggle', () => { if ($radioCor.is(':checked')) setMode('corporate'); });

        const selected = ($root.find(`input[name="${radioName}"]:checked`).val()) || 'individual';
        setMode(selected === 'corporate' ? 'corporate' : 'individual');
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
            root: $('#recipientInfo'),
            radioName: 'userType',
            individualSelector: '#recipientIndividual',
            corporateSelector: '#recipientCorporate',
            sliderSelector: '.radioTab__slider',
        });
    },

    _saveSellerInfo: function () {
        const self = this;
        
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
        }).then((result) => {
            if (result.success && result.partner_id) {
                self.wizard.sellerId = result.partner_id;
            }
            return result;
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
                    self._navigateToStep(self.wizard.currentStep + 1);
                } else {
                    self.displayNotification({ type:'danger', title:'OTP', message: (res && res.message) || 'Doğrulama başarısız' });
                }
            }).catch(()=>{
                self.displayNotification({ type:'danger', title:'OTP', message:'Doğrulama sırasında hata oluştu' });
            });
        });
    },

    _saveProductInfo: function () {
        const self = this;
        return this._saveAdData(true).then((result) => {
            if (result.success && result.id) {
                self.wizard.savedProductId = result.id;
            }
            return result;
        });
    },

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
        vin = vin.toUpperCase();

        if (!/^[A-HJ-NPR-Z0-9]{17}$/.test(vin)) {
            return false;
        }

        const region = vin[0];
        const checkDigit = vin[8];
        const looksLikeChecksum = /^[0-9X]$/.test(checkDigit);
        const requiresChecksum = '12345'.includes(region) || looksLikeChecksum;

        if (!requiresChecksum) {
            return true;
        }

        let sum = 0;
        for (let i = 0; i < vin.length; i++) {
            const c = vin[i];
            const val = map[c];
            if (val === undefined) return false;
            sum += val * weights[i];
        }
        return true;
    },

    _saveCustomerInfo: function() {
        const self = this;
        const userType = $('input[name="userType"]:checked').val();
        const isCardHolderDifferent = $('#checkPoint').is(':checked');

        const data = {
            customer_type: userType,
            is_card_holder_different: isCardHolderDifferent,
        };

        if (this.wizard && this.wizard.savedProductId) {
            data.product_id = this.wizard.savedProductId;
        }

        if (isCardHolderDifferent) {

            data.customer_name_surname = this.customer.input.name_surname.$.val();
            data.customer_identity = this.customer.input.identity.$.val();
            data.customer_phone = this.customer.input.phone_individual.$.val();
            data.customer_email = this.customer.input.email_individual.$.val();
            data.customer_address = this.customer.input.address_individual.$.val();
            
            if (this.wizard && this.wizard.customerID) {
                data.escrow_customer_id = this.wizard.customerID;
            }
        }

        if (userType === 'individual') {
            data.customer_name_surname = this.customer.input.name_surname.$.val();
            data.customer_identity = this.customer.input.identity.$.val();
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

    _checkStep5Parameter: function() {
        const urlParams = new URLSearchParams(window.location.search);
        const step = urlParams.get('step');
        const status = urlParams.get('status');
        const itemId = urlParams.get('item_id');
        
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

    _removeStepParameters: function() {
        const url = new URL(window.location);
        url.searchParams.delete('step');
        url.searchParams.delete('status');
        window.history.replaceState({}, '', url);
    },

    _onToggleDifferentHolder: function(event) {
        const isChecked = event.target.checked;
        const $assignmentSection = this.assignment.form.section.$;
        
        if (isChecked) {
            $assignmentSection.removeClass('d-none').hide().slideDown(300);
        } else {
            $assignmentSection.slideUp(300, function() {
                $(this).addClass('d-none');
            });
        }
        this._navigateToStep(3);
        this._clearCustomerInputs();
    },

    _clearCustomerInputs: function() {
        const $wiz = $('.escrow-wizard');
        $wiz.find('#recipient_name_surname').val('');
        $wiz.find('#recipient_identity').val('');
        $wiz.find('#recipient_phone_individual').val('');
        $wiz.find('#recipient_email_individual').val('');
        $wiz.find('#recipient_address_individual').val('');
        
        $wiz.find('#recipient_corporate_title').val('');
        $wiz.find('#recipient_tax_number').val('');
        $wiz.find('#recipient_tax_office').val('');
        $wiz.find('#recipient_person').val('');
        $wiz.find('#recipient_phone_corporate').val('');
        $wiz.find('#recipient_email_corporate').val('');
        $wiz.find('#recipient_address_corporate').val('');
        
        $wiz.find('.form__control').removeClass('is-invalid -error just-validate-error-field');
        $wiz.find('.form__error-label, .just-validate-error-label').remove();
    },

    _updateCustomer: function(){
        const data = {};
        data.customer_name_surname = this.customer.input.name_surname.$.val();
        data.customer_identity = this.customer.input.identity.$.val();
        data.customer_phone = this.customer.input.phone_individual.$.val();
        data.customer_email = this.customer.input.email_individual.$.val();
        data.customer_address = this.customer.input.address_individual.$.val();
    },

    _onClickReturnToPayment: function(event) {
        event.preventDefault();
        this._navigateToStep(4);
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
                const $wiz = $('.escrow-wizard');
                
                if (customerType === 'individual') {
                    $wiz.find('#recipient_name_surname').val(data.name || '');
                    $wiz.find('#recipient_phone_individual').val(data.phone || '');
                    $wiz.find('#recipient_email_individual').val(data.email || '');
                    $wiz.find('#recipient_address_individual').val(data.address || '');
                } else {
                    $wiz.find('#recipient_corporate_title').val(data.name || '');
                    $wiz.find('#recipient_tax_office').val(data.tax_office || '');
                    $wiz.find('#recipient_person').val(data.contact_person || '');
                    $wiz.find('#recipient_phone_corporate').val(data.phone || '');
                    $wiz.find('#recipient_email_corporate').val(data.email || '');
                    $wiz.find('#recipient_address_corporate').val(data.address || '');
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
