/** @odoo-module alias=paylox.system.vendor **/
'use strict';

import core from 'web.core';
import publicWidget from 'web.public.widget';
import systemPage from 'paylox.system.page';
import systemFlow from 'paylox.system.page.flow';
import fields from 'paylox.fields';

const _t = core._t;

systemFlow.dynamic.include({
    init: function() {
        this._super.apply(this, arguments);
        Object.assign(this.wizard.register, {
            country_id: new fields.integer(),
            company_type: new fields.selection({
                events: [['change', this._onChangeCompanyType]],
            }),
            state_id: new fields.selection(),
            city: new fields.string(),
            street: new fields.string(),
        });
    },

    _queryPartnerPostprocess: function (partner) {
        this._super(partner);
        if (this.advance.exist) {
            $('.payment-system span[name=country]').text(Array.isArray(partner.country_id) ? partner.country_id[1] : partner.country_id || '-');
            $('.payment-system span[name=state]').text(Array.isArray(partner.state) ? partner.state[1] : partner.state || '-');
            $('.payment-system span[name=city]').text(partner.city || '-');
            $('.payment-system span[name=street]').text(partner.street || '-');
            $('.payment-system span[name=phone]').text(partner.phone || '-');
            $('.payment-system span[name=email]').text(partner.email || '-');
        }
    },

    _onChangeCompanyType: function(ev) {
        const label = $('.payment-system input[field="wizard.register.vat"]').parent().find('label span');
        if (ev.val === 'company') {
            label.text(_t('VAT'));
        } else {
            label.text(_t('Vat'));
        }
    }
});

publicWidget.registry.payloxSystemVendor = systemPage.extend({
    selector: '.payment-vendor #wrapwrap',
});
