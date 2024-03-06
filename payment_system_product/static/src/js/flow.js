/** @odoo-module alias=paylox.system.product.flow **/
'use strict';

import { _t } from 'web.core';
import systemFlow from 'paylox.system.page.flow';
import fields from 'paylox.fields';

systemFlow.dynamic.include({
    init: function() {
        this._super.apply(this, arguments);
        Object.assign(this.wizard.button, {
            product: new fields.element({
                events: [['click', this._onClickProduct]],
            }),
        });
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            if (this.wizard.button.product.exist) {
                const products = this.wizard.button.product.$;
                const selected = products.filter((_, e) => $(e).hasClass('btn-primary')).data('id');
                const prices = {}; products.each((_, e) => prices[Number($(e).data('id'))] = Number($(e).data('price')))
                Object.assign(this.wizard.button.product, {
                    prices: prices,
                    selected: Number(selected || 0),
                });
                this._onUpdateProductPrice();
            }
        });
    },

    _onUpdateProductPrice: function() {
        this.wizard.amount.value = this.wizard.button.product.prices[this.wizard.button.product.selected];
        this.wizard.amount._.updateValue();
    },

    _onClickProduct: function(ev) {
        const button = $(ev.currentTarget);
        const buttons = this.wizard.button.product.$;
        buttons.removeClass('btn-primary text-white').addClass('text-primary');
        button.removeClass('text-primary').addClass('btn-primary text-white');
        this.wizard.button.product.selected = Number(button.data('id') || 0);
    },

    _onClickAmountNext: async function () {
        if (this.wizard.button.product.exist) {
            this._onUpdateProductPrice();
        }
        return this._super.apply(this, arguments);
    }
});