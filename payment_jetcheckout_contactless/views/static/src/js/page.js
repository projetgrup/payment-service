/** @odoo-module alias=paylox.page.contactless **/
'use strict';

import rpc from 'web.rpc';
import payloxPage from 'paylox.page';

payloxPage.include({
    init: function (parent, options) {
        this._super(parent, options);
        this.is_contactless = false;
        this.payment = {
            contactless: new fields.element({
                events: [['click', this._onClickPaymentContactless]],
            }),
        }
    },

    _getParams: function () {
        let params = this._super.apply(this, arguments);
        if (is_contactless) {
            params['contactless'] = true;
            this.is_contactless = false;
        }
        return params;
    },

    _onClickPaymentContactless: async function() {
        this.is_contactless = true;
        return this._onClickPaymentButton();
    },
});