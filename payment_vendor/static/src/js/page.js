/** @odoo-module alias=paylox.system.vendor **/
'use strict';

import publicWidget from 'web.public.widget';
import systemPage from 'paylox.system.page';
import systemFlow from 'paylox.system.page.flow';
import fields from 'paylox.fields';

systemFlow.dynamic.include({
    init: function() {
        this._super.apply(this, arguments);
        Object.assign(this.wizard.register, {
            country_id: new fields.integer(),
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
});

publicWidget.registry.payloxSystemVendor = systemPage.extend({
    selector: '.payment-vendor #wrapwrap',
});
