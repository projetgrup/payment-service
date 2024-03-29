/** @odoo-module alias=paylox.page.contactless **/
'use strict';

import fields from 'paylox.fields';
import payloxPage from 'paylox.page';
import framework from 'paylox.framework';

payloxPage.include({
    init: function (parent, options) {
        this._super(parent, options);
        this.is_contactless = false;
        this.payment.contactless = new fields.element({
            events: [['click', this._onClickPaymentContactless]],
        });
    },

    _getParams: function () {
        let params = this._super.apply(this, arguments);
        if (this.is_contactless) {
            params['contactless'] = true;
            this.is_contactless = false;
        }
        return params;
    },

    _checkData: function () {
        let params = this._super.apply(this, arguments);
        this.checklist = [];
        return params;
    },

    _onClickPaymentContactless: function() {
        this.is_contactless = true;
        this.checklist = ['amount', 'agreement'];
        return this._onClickPaymentButton();
    },
});