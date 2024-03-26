/** @odoo-module alias=paylox.system.product.page **/
'use strict';

import { _t, qweb } from 'web.core';
import rpc from 'web.rpc';
import utils from 'web.utils';
import dialog from 'web.Dialog';
import publicWidget from 'web.public.widget';

import fields from 'paylox.fields';
import payloxPage from 'paylox.page';
import framework from 'paylox.framework';
import systemPage from 'paylox.system.page';
import { format } from 'paylox.tools';

payloxPage.include({

    init: function (parent, options) {
        this._super(parent, options);
        this.state = {
            product: {
                payment: false,
            }
        };
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            if (this.options.product) {
                window.addEventListener('payment-started', () => {
                    this.state.product.payment = true;
                    this._getInstallment();
                });
                window.addEventListener('payment-stopped', () => {
                    this.state.product.payment = false;

                    this.installment.colempty.$.removeClass('d-none');
                    this.installment.col.$.addClass('d-none');
                    this.installment.col.html = '';
                    this.installment.cols = [];
    
                    this.installment.rowempty.$.removeClass('d-none');
                    this.installment.row.$.addClass('d-none');
                    this.installment.row.html = '';
                    this.installment.rows = [];
    
                    this.card.logo.html = '';
                    this.card.logo.$.removeClass('show');
                    this.card.bin = '';
                    this.card.family = '';
                });
            }
        });
    },

    _checkData: function () {
        if (this.options.product) {
            if (!this.state.product.payment) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('Price lock has been removed.\nPlease start the payment procedure all over.'),
                });
                this._enableButton();
                return false;
            }
        } else {
            return this._super.apply(this, arguments);
        }
    },

    _getParams: function () {
        let params = this._super.apply(this, arguments);
        let $products = $('.base[field="product.qty"]').filter((i, e) => e.value > 0);
        if ($products.length) {
            let products = [];
            $products.each((i, e) => {
                products.push({
                    'pid': e.dataset.id,
                    'qty': e.value,
                })
            });
            params['products'] = products;
        }        
        return params;
    },
});

publicWidget.registry.payloxSystemProduct = systemPage.extend({
    selector: '.payment-product #wrapwrap',
    xmlDependencies: [
        '/payment_system_product/static/src/xml/page.xml',
        '/payment_jetcheckout_system/static/src/xml/system.xml',
    ],

    init: function (parent, options) {
        this._super(parent, options);
        this._listenPriceActive = false;
        this._saveOrderActive = false;
        this._saveOrderTime = undefined;
        this._saveOrder = _.debounce(this._save, 1000);

        this.lines = {};
        this.brands = {};
        this.products = {};
        this.locked = false;
        this.validity = 0;
        this.commission = 0;
        this.options = new fields.element();
        this.product = {
            price: new fields.float({
                default: 0,
            }),
            qty: new fields.integer({
                default: 0,
                events: [['change', this._onChangeQty]],
            }),
            amount: new fields.float({
                default: 0,
            }),
            validity: new fields.float({
                default: 0,
            }),
            commission: new fields.float({
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
            counter: new fields.element(),
            items: new fields.element(),
            lines: new fields.element(),
            item: new fields.element({
                events: [['click', this._onClickItem]],
            }),
            categ: new fields.element({
                events: [['click', this._onClickCateg]],
            }),
            plus: new fields.element({
                events: [['click', this._onClickPlus]],
            }),
            minus: new fields.element({
                events: [['click', this._onClickMinus]],
            }),
            brands: new fields.element({
                events: [['click', this._onClickBrands]],
            }),
            policy: new fields.element({
                events: [['click', this._onClickPolicy]],
            }),
            pay: new fields.element({
                events: [['click', this._onClickPay]],
            }),
            back: new fields.element({
                events: [['click', this._onClickBack]],
            }),
            share: new fields.element({
                events: [['click', this._onClickShare]],
            }),
        }
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            this._getOptions();
            this._getNumbers();
            this._getBrands();
            this._getProducts();
            this._processParams();
            this._updateLines();
            this._listenPrices();
        });
    },

    _save: function (values) {
        if (this._saveOrderActive) {
            rpc.query({
                route: '/my/order',
                params: { values },
            }).then((res) => {
                this._saveOrderTime = Date.now();
            }).catch((err) => {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured.'),
                });
            });
        }
    },

    _getOptions: function () {
        this._listenPriceActive = this.options.json.listen_price_active;
        this._saveOrderActive = this.options.json.save_order_active;
        this.options.$.remove();
    },

    _getNumbers: function () {
        this.validity = this.product.validity.value; this.product.validity.$.remove();
        this.commission = this.product.commission.value; this.product.commission.$.remove();
    },

    _getBrands: function () {
        let $brands = $('[field="product.brands"]');
        $brands.each((i, e) => {
            let bid = e.dataset.id;
            let pid = e.dataset.product;
            if (!(pid in this.brands)) {
                this.brands[pid] = {};
            }
            this.brands[pid][bid] = {
                id: parseInt(bid),
                name: e.dataset.name,
                image: e.dataset.image,
            }
        });
    },

    _getProducts: function () {
        let $products = $('[field="product.items"]');
        $products.each((i, e) => {
            let pid = e.dataset.id;
            this.products[pid] = {
                id: parseInt(pid),
                name: e.dataset.name,
                foreground: e.dataset.foreground,
                background: e.dataset.background,
            }
        });
    },

    _processParams: function () {
        const params = new URLSearchParams(window.location.search);
        for (const param of params) {
            if (!param[0]) {
                const values = JSON.parse(atob(param[1]));
                if ('products' in values) {
                    const categs = new Set();
                    this.product.qty.$.each((i, e) => {
                        const item = e.closest('[field="product.items"]');
                        if (e.dataset.id in values['products']) {
                            e.value = values['products'][e.dataset.id];
                            e.disabled = true;
                            this._onChangeQty({ currentTarget: e }, false);
                            categs.add(item.dataset.categ);
                        } else {
                            item.remove();
                        }
                    });
                    this.product.categ.$.each((i, e) => {
                        if (!categs.has(e.value)) {
                            e.parentNode.remove();
                        }
                    });
                    this._updateLines();
                    this.locked = true;
                }
                break;
            }
        }

    },

    _listenPrices: function () {
        if (this.locked) return;

        if (this._listenPriceActive) {
            const events = new EventSource('/longpolling/prices');
            console.log('Price service is active.');
            events.onmessage = (event) => {
                let changed = false;
                let $prices = this.product.price.$;
                let currency = [this.currency.position, this.currency.symbol, this.currency.decimal];
                for (let data of event.data.split('\n')) {
                    let [code, price] = data.split(';'); price = parseFloat(price);
                    let $price = $prices.filter(`[data-id="${code}"]`);
                    let value = $price.data('value');
                    if (price == value) {
                        continue;
                    } else if (price > value) {
                        $price.css({ backgroundColor: '#93daa3' });
                    } else if (price < value) {
                        $price.css({ backgroundColor: '#eccfd1' });
                    }
    
                    changed = true;
                    $price.animate({ backgroundColor: '#ffffff' }, 'slow');
                    $price.data('value', price);
                    $price.text(format.currency(price, ...currency));
                    this._onChangePrice($price, false);
                }
                if (changed) {
                    this._updateLines();
                }
            };
            events.onerror = () => {
                console.error('An error occured on price service. Reconnecting...');
                events.close();
                setTimeout(this._listenPrices.bind(this), 10000);
            };
        }
    },

    _onChangePrice($price, update=true) {
        if (this.locked) return;

        let $qty = this.product.qty.$.filter(`.base[data-id=${$price.data('id')}]`);
        let $amount = this.product.amount.$.filter(`[data-id=${$price.data('id')}]`);

        let qty = parseFloat($qty.val());
        let price = parseFloat($price.data('value'));
        let value = qty * price;

        $amount.data('qty', qty);
        $amount.data('price', price);
        $amount.data('value', value);
        $amount.text(format.currency(value, this.currency.position, this.currency.symbol, this.currency.decimal));

        if (update) {
            this._updateLines();
        }
    },

    _updateLines() {
        if (this.locked) return;
        if (this.timeout) return;

        let subtotal = 0;
        let brands = {};
        let currency = [this.currency.position, this.currency.symbol, this.currency.decimal];
        this.product.amount.$.filter(`.base`).each((i, e) => {
            let $e = $(e);
            let value = parseFloat($e.data('value'));
            if (value > 0) {
                let vid = $e.data('id') || 0;
                let bid = $e.data('brand') || 0;
                let pid = $e.data('product') || 0;
                let qty = parseFloat($e.data('qty') || 0);
                let price = parseFloat($e.data('price') || 0);
                let weight = parseFloat($e.data('weight') || 0);
                this.lines[vid] = { pid: vid, price, qty };

                if (!(bid in brands)) {
                    brands[bid] = { products: {}, name: this.brands?.[pid]?.[bid]?.['name'] || '' };
                }
                if (!(pid in brands[bid]['products'])) {
                    brands[bid]['products'][pid] = { weight: 0, value: 0, name: this.products[pid]['name'] };
                }
                brands[bid]['products'][pid]['weight'] += qty * weight;
                brands[bid]['products'][pid]['value'] += value;
                subtotal += value;
            }
        });

        this.product.brands.$.each((i, e) => {
            let $e = $(e);
            let $span = $e.find('span');
            let bid = parseInt($e.data('id'));
            let pid = parseInt($e.data('product'));

            let weight = brands?.[bid]?.['products']?.[pid]?.['weight'];
            if (weight) {
                $span.removeClass('d-none');
                $span.text(weight);
            } else {
                $span.addClass('d-none');
            }
        });

        brands = Object.values(brands);
        for (let brand of brands) {
            brand.products = Object.values(brand.products);
        }

        this.product.lines.html = qweb.render('paylox.product.lines', {
            format,
            brands,
            currency: this.currency,
        });

        let fee = subtotal * this.commission;
        let total = subtotal + fee;
        this.amount.value = format.float(total);
        this.amount.$.trigger('update');

        this.product.subtotal.text = format.currency(subtotal, ...currency);
        this.product.fee.text = format.currency(fee, ...currency);
        this.product.total.text = format.currency(total, ...currency);

        this._saveOrder({ lines: Object.values(this.lines) });
    },

    _onChangeQty(ev, update=true) {
        if (this.locked) return;

        let $qty = $(ev.currentTarget);
        let pid = $qty.data('id');
        this.product.qty.$.filter(`[data-id=${pid}]`).val($qty.val());

        let $price = this.product.price.$.filter(`.base[data-id=${pid}]`);
        let $amount = this.product.amount.$.filter(`[data-id=${pid}]`);

        let qty = parseFloat($qty.val());
        let price = parseFloat($price.data('value'));
        let value = qty * price;

        $amount.data('qty', qty);
        $amount.data('value', value);
        $amount.text(format.currency(value, this.currency.position, this.currency.symbol, this.currency.decimal));

        if (update) {
            this._updateLines();
        }
    },

    _onClickItem(ev) {
        if (this.locked) return;

        this.product.qty.$.val(0);
        this.product.item.$.removeClass('bg-warning');

        let btn = $(ev.currentTarget);
        let pid = btn.data('id');
        let qty = this.product.qty.$.filter(`.base[data-id=${pid}]`);

        qty.val(1);
        btn.addClass('bg-warning');

        this.product.qty.$.each((i, e) => this._onChangeQty({ currentTarget: e }, false))
        this._updateLines();
    },

    _onClickCateg(ev) {
        const categ = ev.currentTarget.value;
        this.product.items.$.each((_, e) => {
            if (e.dataset.categ === categ) {
                e.classList.remove('d-none');
            } else {
                e.classList.add('d-none');
            }
        });
    },

    _onClickPlus(ev) {
        if (this.locked) return;

        let btn = $(ev.currentTarget);
        let pid = btn.data('id');
        let qty = this.product.qty.$.filter(`.base[data-id=${pid}]`);

        let val = qty.val();
        qty.val(+val+1);
        qty.trigger('change');
    },

    _onClickMinus(ev) {
        if (this.locked) return;

        let btn = $(ev.currentTarget);
        let pid = btn.data('id');
        let qty = this.product.qty.$.filter(`.base[data-id=${pid}]`);

        let val = qty.val();
        if (val > 0) {
            qty.val(+val-1);
        } else {
            qty.val(0);
        }
        qty.trigger('change');
    },

    _onClickBrands(ev) {
        let $btn = $(ev.currentTarget);
        let $item = this.product.items.$.filter(`[data-id=${ $btn.data('product') }]`);
        if ($btn.hasClass('base')) {
            $item.find(`[data-brand]`).each((i, e) => $(e).addClass('d-none'));
            $item.find(`[data-brand=${ $btn.data('id') }]`).each((i, e) => $(e).removeClass('d-none'));
    
            this.product.brands.$.filter(`[data-product=${ $btn.data('product') }]`).removeClass('active');
            this.product.brands.$.filter(`[data-product=${ $btn.data('product') }][data-id=${ $btn.data('id') }]`).each((i, e) => $(e).addClass('active'));
        } else {   
            let pid = parseInt($item.data('id'));
            let brands = Object.values(this.brands[pid]);
            let foreground = $item.data('foreground');
            let background = $item.data('background');
            let popup = new dialog(this, {
                size: 'small',
                title: _t('Choose a brand'),
                $content: qweb.render('paylox.product.brands', { brands, foreground, background }),
            });
            popup.open().opened(() => {
                popup.$modal.addClass('payment-product-brand-popup');
                popup.$modal.find('.modal-header').attr('style', `color:${foreground} !important;background-color:${background} !important`);
                popup.$modal.find('.modal-footer button').attr('style', `color:${foreground} !important;background-color:${background} !important`);
                popup.$modal.find('button').click((e) => {
                    let bid = parseInt(e.currentTarget.dataset.id);
                    if (!isNaN(bid)) {
                        $item.find(`[data-brand]`).each((i, e) => $(e).addClass('d-none'));
                        $item.find(`[data-brand=${ bid }]`).each((i, e) => $(e).removeClass('d-none'));
                
                        this.product.brands.$.filter(`[data-product=${ $btn.data('product') }]`).removeClass('active');
                        this.product.brands.$.filter(`[data-product=${ $btn.data('product') }][data-id=${ bid }]`).each((i, e) => $(e).addClass('active'));
                    }
                    popup.close();
                });
            });
        }
    },

    _onClickPolicy() {
        framework.showLoading();
        rpc.query({
            route: '/my/product/policy',
        }).then((partner) => {
            let popup = new dialog(this, {
                size: 'small',
                technical: false,
                title: _t('My PoS Policy'),
                $content: qweb.render('paylox.product.policy', partner),
            });
            popup.open().opened(() => {
                let $loading = popup.$modal.find('.loading');
                popup.$modal.addClass('payment-product-policy-popup');
                popup.$modal.find('.modal-body button').click(() => {
                    $loading.addClass('show');
                    rpc.query({
                        route: '/my/product/policy/send',
                    }).then((result) => {
                        if (result.error) {
                            this.displayNotification({
                                type: 'danger',
                                title: _t('Error'),
                                message: result.error,
                            });
                        } else {
                            this.displayNotification({
                                type: 'info',
                                title: _t('Success'),
                                message: _t('Policy has been sent succesfully.'),
                            });
                            popup.close();
                        }
                        $loading.removeClass('show');
                    }).guardedCatch(() => {
                        this.displayNotification({
                            type: 'danger',
                            title: _t('Error'),
                            message: _t('An error occured. Please contact with your system administrator.'),
                        });
                        $loading.removeClass('show');
                    });
                });
            });
            framework.hideLoading();
        }).guardedCatch(() => {
            this.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please contact with your system administrator.'),
            });
            framework.hideLoading();
        });
    },

    _onClickPay(ev) {
        $(document.body).addClass(['payment-form', this.validity > 0 ? 'payment-counter' : '']);
        $(ev.currentTarget).addClass('hide');
        this.product.back.$.removeClass('hide');
        this.product.share.$.addClass('hide');
        this._startPayment();
    },

    _onClickBack(ev) {
        $(document.body).removeClass(['payment-form', this.validity > 0 ? 'payment-counter' : '']);
        $(ev.currentTarget).addClass('hide');
        this.product.pay.$.text(_t('Pay Now'));
        this.product.pay.$.removeClass('hide');
        this.product.share.$.removeClass('hide');
        this._stopPayment();
    },

    _onClickShare(ev) {
        this._onClickLink(ev);
    },

    _onClickLink: async function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const websiteID = $('html').data('websiteId') || 0;
        const products = {};
        for (const line of Object.values(this.lines)) {
            products[line.pid] = line.qty;
        }
        const params = JSON.stringify({
            id: websiteID,
            products,
        })

        let link = window.location.origin + window.location.pathname + '?=' + encodeURIComponent(btoa(params));
        navigator.clipboard.writeText(link);

        let content = qweb.render('paylox.item.link', { link });
        await this.displayNotification({
            type: 'info',
            title: _t('Payment link is ready'),
            message: utils.Markup(content),
            sticky: true,
        });
        setTimeout(() => {
            $('.o_notification_body .o_button_link_send').off('click').on('click', (ev) => {
                rpc.query({
                    model: 'res.partner',
                    method: 'send_payment_link',
                    args: [ev.currentTarget.dataset.type, link],
                }).then((result) => {
                    if ('error' in result) {
                        this.displayNotification({
                            type: 'warning',
                            title: _t('Warning'),
                            message: _t('An error occured.') + ' ' + result.error,
                        });
                    } else {
                        this.displayNotification({
                            type: 'info',
                            title: _t('Success'),
                            message: result.message,
                        });
                    }
                }).guardedCatch((error) => {
                    this.displayNotification({
                        type: 'danger',
                        title: _t('Error'),
                        message: _t('An error occured. Please contact with your system administrator.'),
                    });
                    if (config.isDebug()) {
                        console.error(error);
                    }
                });
            });
        }, 1000);
    },

    _startPayment() {
        this._saveOrder({ lock: true });
        if (this.validity > 0) {
            const $counter = this.product.counter.$.find('svg');
            const $progress = $counter.find('.progress');
            const counter = () => {
                if (this.timeout <= 0) {
                    this.product.pay.$.text(_t('Restart Payment'));
                    this.product.pay.$.removeClass('hide');
                    this._stopPayment();
                    return;
                }
    
                $counter.next().text(--this.timeout);
                $progress.css('stroke-dashoffset', 400 - 400 * this.timeout / this.validity);
            }

            this.timeout = this.validity + 1; counter();
            this.interval = setInterval(counter, 1000);
    
            $('[field="installment.table"] button').removeClass('disabled').removeAttr('disabled');
            $('[field="campaign.table"] button').removeClass('disabled').removeAttr('disabled');
            $('[field="payment.button"]').removeClass('disabled').removeAttr('disabled');
            window.dispatchEvent(new Event('payment-started'));
        }
    },

    _stopPayment() {
        if (this.validity > 0) {
            this.timeout = undefined;
            clearInterval(this.interval);
    
            $('[field="installment.table"] button').addClass('disabled').attr('disabled', 'disabled');
            $('[field="campaign.table"] button').addClass('disabled').attr('disabled', 'disabled');
            $('[field="payment.button"]').addClass('disabled').attr('disabled', 'disabled');
            window.dispatchEvent(new Event('payment-stopped'));
        }
        this._updateLines();
    },
});
