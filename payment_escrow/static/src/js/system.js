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
        const urlParams = new URLSearchParams(window.location.search);
        const urlItemId = urlParams.get('item_id');
        const urlProductId = urlParams.get('product_id');
        
        if (urlItemId && urlProductId) {
            const itemId = parseInt(urlItemId, 10) || 0;
            const productId = parseInt(urlProductId, 10) || 0;
            
            if (itemId && productId) {
                let amount = 0;
                const $partial = $('#paymentAmount');
                if ($partial.length) {
                    const raw = parse($partial.val());
                    if (raw > 0) amount = raw;
                }
                
                if (!amount) {
                    const $selectedAd = $(`[data-id="${productId}"]`);
                    if ($selectedAd.length) {
                        const residual = parse($selectedAd.attr('data-item-residual-amount'));
                        const domAmount = parse($selectedAd.attr('data-item-amount'));
                        const price = parse($selectedAd.find('.escrow-ad-item-price').attr('data-value'));
                        if (residual > 0) amount = residual;
                        else if (domAmount > 0) amount = domAmount;
                        else if (price > 0) amount = price;
                    }
                }
                
                payments.push(itemId);
                items.push([itemId, amount]);
                products.push({ pid: productId, qty: 1 });
                
                return { items, payments, products };
            }
        }
    },
});
