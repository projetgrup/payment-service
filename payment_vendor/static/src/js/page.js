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
            company_type: new fields.string(),
            tax_office_id: new fields.selection(),
            state_id: new fields.selection(),
            city: new fields.string(),
            street: new fields.string(),
            buttons: {
                company_type: new fields.element({
                    events: [['click', this._onClickCompanyType]],
                }),
            }
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

    _onClickCompanyType: function(ev) {
        const button = $(ev.currentTarget);
        const buttons = $('.payment-system button[field="wizard.register.buttons.company_type"]');
        buttons.removeClass('selected').find('input').prop({'checked': false});
        button.addClass('selected').find('input').prop({'checked': true});

        const type = button.attr('name');
        this.wizard.register.company_type.value = type;

        const name = this.wizard.register.name.$.parent().find('label span');
        const vat = this.wizard.register.vat.$.parent().find('label span');
        const office = this.wizard.register.tax_office_id;
        if (type === 'company') {
            name.text(_t('Company Name'));
            vat.text(_t('VAT'));
            office.$.parent().removeClass('d-none');
        } else {
            name.text(_t('Name'));
            vat.text(_t('Vat'));
            office.value = '';
            office.$.parent().addClass('d-none');
        }
    },
});

publicWidget.registry.payloxSystemVendor = systemPage.extend({
    selector: '.payment-vendor #wrapwrap',
});
