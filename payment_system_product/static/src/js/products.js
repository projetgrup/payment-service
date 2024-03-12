/** @odoo-module alias=paylox.system.products **/
'use strict';

import { _t } from 'web.core';
import rpc from 'web.rpc';
import publicWidget from 'web.public.widget';
import { format } from 'paylox.tools';
import framework from 'paylox.framework';

publicWidget.registry.payloxSystemProductsPage = publicWidget.Widget.extend({
    selector: '.o_portal_payment_products',
    events: {
        'click tfoot button': '_onClickSave',
        'input tbody input': '_onChangeInput',
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            $('.o_portal').append($(`
                <div class="o_loading">
                    <em class="fa fa-spin fa-circle-o-notch text-primary h1"/>
                </div>
            `));
        });
    },

    _onChangeInput: function(ev) {
        const input = ev.currentTarget;
        const margin = Number(input.value);
        const price = Number(input.dataset.value);
        const total = document.querySelector(`span[data-id="${input.dataset.id}"] span`);
        total.innerHTML = format.float(price * (100 + margin) / 100);
    },

    _onClickSave: function(ev) {
        framework.showLoading();

        const products = {};
        $('tbody input').each((i, e) => {
            const $e = $(e);
            const pid = Number($e.data('id'));
            const val = Number($e.val());
            products[pid] = val;
        });

        rpc.query({
            route: '/my/products/save',
            params: { products },
        }).then((result) => {
            if ('error' in result) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: result['error'],
                });
            } else {
                this.displayNotification({
                    type: 'info',
                    title: _t('Success'),
                    message: _t('All changes have been saved.'),
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
    }
});