/** @odoo-module alias=escrow.system **/
'use strict';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';

payloxPage.include({
    init: function (parent, options) {
        this._super(parent, options);
        this.system = new fields.string({
            default: 'escrow',
        });
    },
    
    _getParams: function() {
        const params = this._super.apply(this, arguments);
        const { items, payments, products } = this._getEscrowItems();
        params.system = 'escrow';
        params.items = items;
        params.payments = payments;
        if (products.length) params.products = products;
        return params;
    },

    _getEscrowItems: function () {
        const items = [];
        const payments = [];
        const products = [];

        const parse = (v) => {
            if (v == null) return 0;
            const n = parseFloat(String(v).replace(/\./g, '').replace(',', '.'));
            return isNaN(n) ? 0 : n;
        };

        let adId = 0;
        const $cont = $('.escrow-ad-button-continue');
        if ($cont.length) adId = parseInt($cont.data('id') || 0, 10) || 0;
        if (!adId) {
            const $ads = $('[field="ad.item"]');
            if ($ads.length) adId = parseInt($ads.first().data('id') || 0, 10) || 0;
        }

        if (!adId) return { items, payments, products };

        const $ad = $(`[field="ad.item"][data-id="${adId}"]`);
        const itemId = parseInt(($ad.attr('data-item-id') || 0), 10) || 0;
        const productId = parseInt(($ad.attr('data-product-id') || 0), 10) || 0;

        let amount = 0;
        const $partial = $('#paymentAmount');
        if ($partial.length) {
            const raw = parse($partial.val());
            if (raw > 0) amount = raw;
        }
        if (!amount && $ad.length) {
            const residual = parse($ad.attr('data-item-residual-amount'));
            const domAmount = parse($ad.attr('data-item-amount'));
            const price = parse($ad.find('.escrow-ad-item-price').attr('data-value'));
            if (residual > 0) amount = residual;
            else if (domAmount > 0) amount = domAmount;
            else if (price > 0) amount = price;
        }

        if (itemId) {
            payments.push(itemId);
            items.push([itemId, amount]);
        }
        if (productId) {
            products.push({ pid: productId, qty: 1 });
        }

        return { items, payments, products };
    },
});
