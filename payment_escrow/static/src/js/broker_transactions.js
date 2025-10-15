/** @odoo-module alias=paylox.system.escrow.broker.transaction **/
'use strict';

import rpc from 'web.rpc';
import { _t } from 'web.core';
import publicWidget from 'web.public.widget';
import payloxPage from 'paylox.page';
import framework from 'paylox.framework';
import fields from 'paylox.fields';


publicWidget.registry.payloxBrokerTransaction = payloxPage.extend({
    selector: '.broker-transactions #wrapwrap',
    jsLibs: [
        '/payment_jetcheckout/static/src/lib/imask/imask.js',
        '/payment_jetcheckout/static/src/lib/filepond/filepond.js',
    ],

    init: function (parent, options) {
        this._super(parent, options);
        this.transactions = {
            invoiceFile: new fields.file({
                name: 'invoiceFile',
                allowMultiple: false,
                accept: 'image/*, application/pdf',
                maxFileSize: '10MB',
                className: 'escrow-wizard-file',
                labelIdle: `<svg class="w-100" width="42" height="42" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M31.4998 33.2514C30.5318 33.2514 29.7484 32.468 29.7484 31.5C29.7484 30.532 30.5318 29.7486 31.4998 29.7486C35.3594 29.7486 38.5012 26.6068 38.5012 22.7473C38.5012 19.0723 35.626 16.0084 31.9592 15.7705L30.9256 15.709L30.4867 14.7779C28.7559 11.1152 25.0316 8.74863 20.9998 8.74863C16.968 8.74863 13.2438 11.1152 11.5129 14.7779L11.074 15.709L10.0445 15.7746C6.37363 16.0125 3.50254 19.0764 3.50254 22.7514C3.50254 26.6109 6.64434 29.7527 10.5039 29.7527C11.4719 29.7527 12.2553 30.5361 12.2553 31.5041C12.2553 32.4721 11.4719 33.2555 10.5039 33.2555C4.7125 33.2555 0.00390625 28.5469 0.00390625 22.7555C0.00390625 17.5834 3.79785 13.2193 8.80996 12.4031C11.2709 8.02676 15.9508 5.25 20.9998 5.25C26.0488 5.25 30.7287 8.02676 33.1938 12.3949C38.2059 13.2111 41.9998 17.5793 41.9998 22.7514C41.9998 28.5387 37.2912 33.2514 31.4998 33.2514Z" fill="black"/>
                        <path d="M26.2502 32.3737C25.8032 32.3737 25.3561 32.2014 25.0116 31.861L21.0002 27.8497L16.9889 31.861C16.3081 32.5459 15.1965 32.5459 14.5157 31.861C13.8307 31.176 13.8307 30.0686 14.5157 29.3877L19.7657 24.1377C20.4465 23.4528 21.5581 23.4528 22.2389 24.1377L27.4889 29.3877C28.1739 30.0727 28.1739 31.1801 27.4889 31.861C27.1444 32.2055 26.6973 32.3737 26.2502 32.3737Z" fill="#2414D8"/>
                        <path d="M21.0004 39.375C20.0324 39.375 19.249 38.5916 19.249 37.6236V25.3764C19.249 24.4084 20.0324 23.625 21.0004 23.625C21.9684 23.625 22.7518 24.4084 22.7518 25.3764V37.6277C22.7518 38.5916 21.9684 39.375 21.0004 39.375Z" fill="#2414D8"/>
                    </svg>
                    <span class="text-600">Fatura Yükle</span>
                    <div class="text-600">PDF veya Resim</div>`,
                validate: () => {
                    return !!this.transactions.invoiceFile.value;
                },
            }),
            submitButton: new fields.element({
                events: [['click', this._onSubmitInvoice]]
            }),
        }
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);
            framework.hideLoading();
            setTimeout(() => $('div.o_loading').addClass('transparent'), 2000);
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handle invoice file submission
     * @private
     * @param {Event} ev
     */
    _onSubmitInvoice: function(ev) {
        ev.preventDefault();
        const self = this;
        const $button = $(ev.currentTarget);
        const $form = $button.closest('form');
        const $modal = $button.closest('.modal');
        
        // Validate file
        if (!this.transactions.invoiceFile.value) {
            alert(_t('Lütfen fatura dosyası seçiniz'));
            return;
        }

        // Get file from FilePond
        const base64Data = this.transactions.invoiceFile.value;
        const files = this.transactions.invoiceFile._.getFiles();
        
        if (!files || files.length === 0) {
            alert(_t('Dosya bulunamadı'));
            return;
        }

        const file = files[0];

        // Disable button
        $button.prop('disabled', true).html('<i class="fa fa-spinner fa-spin mr-1"></i>Yükleniyor...');

        // Submit via RPC
        this._rpc({
            route: $form.attr('action'),
            params: {
                invoice_file: base64Data,
                filename: file.filename,
                mimetype: file.fileType,
            }
        }).then(function(response) {
            if (response.success) {
                $modal.modal('hide');
                window.location.reload();
            } else {
                alert(response.message || _t('Fatura yüklenirken hata oluştu'));
                $button.prop('disabled', false).html('<i class="fa fa-upload mr-1"></i>Upload');
            }
        }).guardedCatch(function() {
            alert(_t('Fatura yüklenirken hata oluştu'));
            $button.prop('disabled', false).html('<i class="fa fa-upload mr-1"></i>Upload');
        });
    },

});