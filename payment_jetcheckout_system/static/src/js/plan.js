/** @odoo-module alias=paylox.plan.pay.page **/
'use strict';

import { _t } from 'web.core';
import dialog from 'web.Dialog';
import fields from 'paylox.fields';
import payloxPage from 'paylox.page';
import framework from 'paylox.framework';
import publicWidget from 'web.public.widget';

publicWidget.registry.payloxPlanResult = publicWidget.Widget.extend({
    selector: '.payment-plan-result #wrapwrap',

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            setTimeout(() => {
            const redirect = document.getElementById('redirect');
                if (redirect) {
                    if (redirect.value) {
                        window.location.href = redirect.value;
                    } else {
                        window.parent.document.querySelector('.o_form_payment_plan_pay').closest('.modal-content').querySelector('header button.close').click();
                    }
                }
            }, 2000);
        });
    },
});

publicWidget.registry.payloxPlanPage = publicWidget.Widget.extend({
    selector: '.payment-plan',
    //xmlDependencies: ['/payment_jetcheckout_system/static/src/xml/plan.xml'],

    init: function (parent, options) {
        this._super(parent, options);
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
            default: 0,
        });
        this.partner = new fields.integer({
            default: 0,
        });
        this.payment = {
            plan: new fields.element({
                events: [['change', this._onChangePlan]],
            }),
            plans: new fields.element({
                events: [['change', this._onChangePlans]],
            }),
        };
        this.button = {
            confirm: new fields.element({
                events: [['click', this._onClickConfirm]],
            }),
        };
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);
            if (this.payment.plan.exist) {
                this._onChangePlan();
            }

            this.button.confirm.text = _t('I approve all of the payment plans');
            this.button.confirm.$.addClass('show');
            framework.hideLoading();
        });
    },

    _onChangePlan: function (ev) {
        if (ev && ev.currentTarget) {
            let $input = $(ev.currentTarget);
            let $action = $input.parent().next();
            if ($input.is(':checked')) {
                $action.text(_t('Approve'));
                $action.removeClass('text-danger').addClass('text-primary');
            } else {
                $action.text(_t('Disapprove'));
                $action.removeClass('text-primary').addClass('text-danger');
            }
        }

        let $plans = $('input.input-switch:checked');
        this.payment.plans.checked = !!$plans.length;
    },

    _onChangePlans: function (ev) {
        let checked = $(ev.currentTarget).is(':checked');
        let $inputs = this.payment.plan.$;
        $inputs.prop('checked', checked);
        $inputs.trigger('change');
    },

    _onClickConfirm: function () {
        new dialog(self, {
            title: _t('Warning'),
            size: 'small',
            buttons: [{
                close: true,
                text: _t('Cancel'),
                classes: 'btn-secondary text-white',
            }, {
                text: _t('Remove'),
                classes: 'btn-danger text-white',
                click: () => {}
            }],
            //$content: qweb.render('paylox.campaigns', { campaigns, current: this.campaign.name.value })
        }).open();
    },
});

export default publicWidget.registry.payloxTokenVerify;
