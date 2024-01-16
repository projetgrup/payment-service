/** @odoo-module alias=paylox.system.jewelry **/
'use strict';

import publicWidget from 'web.public.widget';
import core from 'web.core';
import rpc from 'web.rpc';
import fields from 'paylox.fields';
import framework from 'paylox.framework';
import systemPage from 'paylox.system.page';
import { format } from 'paylox.tools';

const _t = core._t;
const Qweb = core.qweb;

publicWidget.registry.payloxSystemJewelry = systemPage.extend({
    selector: '.payment-jewelry #wrapwrap',
    xmlDependencies: ['/payment_jewelry/static/src/xml/page.xml'],

    init: function (parent, options) {
        this._super(parent, options);
        this.jewelry = {
            price: new fields.float({
                default: 0,
            }),
            qty: new fields.integer({
                default: 0,
                events: [['change', this._onChangeJewelryQty]],
            }),
            amount: new fields.float({
                default: 0,
            }),
            subtotal: new fields.float({
                default: 0,
            }),
            fee: new fields.float({
                default: 0,
            }),
            total: new fields.float({
                default: 0,
            }),
            lines: new fields.element({
            }),
            pay: new fields.element({
            }),
        }
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this._updateJewelryLines();
        });
    },

    _onChangeJewelryQty(ev) {
        let $input = $(ev.currentTarget);
        let $price = this.jewelry.price.$.filter(`[data-id=${$input.data('id')}]`);
        let $amount = this.jewelry.amount.$.filter(`[data-id=${$input.data('id')}]`);

        let qty = parseFloat($input.val());
        let price = parseFloat($price.data('value'));
        let value = qty * price;

        $amount.data('qty', qty);
        $amount.data('value', value);
        $amount.text(format.currency(value, this.currency.position, this.currency.symbol, this.currency.decimal));

        this._updateJewelryLines();
    },

    _updateJewelryLines() {
        let subtotal = 0;
        let products = {};
        let currency = [this.currency.position, this.currency.symbol, this.currency.decimal];
        this.jewelry.amount.$.each(function (i, e) {
            let $e = $(e);
            let value = parseFloat($e.data('value'));
            if (value > 0) {
                let name = $e.data('name');
                let qty = parseFloat($e.data('qty'));
                let weight = parseFloat($e.data('weight'));
                if (!(name in products)) {
                    products[name] = { weight: 0, value: 0 };
                }
                products[name].weight += qty * weight;
                products[name].value += value;
                subtotal += value;
            }
        });
        this.jewelry.lines.html = Qweb.render('paylox.jewelry.lines', {
            format,
            currency: this.currency,
            products: Object.entries(products),
        });

        let fee = subtotal * 0.04;
        let total = subtotal + fee;
        this.jewelry.subtotal.text = format.currency(subtotal, ...currency);
        this.jewelry.fee.text = format.currency(fee, ...currency);
        this.jewelry.total.text = format.currency(total, ...currency);
    },
});
