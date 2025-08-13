/** @odoo-module alias=paylox.system.escrow **/
'use strict';

import core from 'web.core';
import publicWidget from 'web.public.widget';
import framework from 'paylox.framework';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';
import { format } from 'paylox.tools';

const _t = core._t;

publicWidget.registry.payloxSystemEscrow = publicWidget.Widget.extend({
    selector: '.payment-escrow #wrapwrap',

    init: function (parent, options) {
        this._super(parent, options);
        this.values = {
            ads: {},
        };
        this.currency = {
            id: 0,
            decimal: 2,
            name: '',
            separator: '.',
            thousand: ',', 
            position: 'after',
            symbol: '', 
        };
        this.partner = new fields.integer({
            default: 0,
        });
        this.ad = {
            sidebar: new fields.element(),
            sideback: new fields.element({
                events: [['click', this._onClickSideback]],
            }),
            button: {
                sidebar: {
                    toggle: new fields.element({
                        events: [['click', this._onClickButtonSidebarToggle]],
                    }),
                },
                list: new fields.element({
                    events: [['click', this._onClickButtonList]],
                }),
                grid: new fields.element({
                    events: [['click', this._onClickButtonGrid]],
                }),
                form: new fields.element({
                    events: [['click', this._onClickButtonForm]],
                }),
                discard: new fields.element({
                    events: [['click', this._onClickButtonDiscard]],
                }),
            },
            input: {
                img: new fields.element(),
                name: new fields.string(),
                desc: new fields.html({
                    parent: this,
                }),
                categ: new fields.selection(),
                price: new fields.float({
                    mask: payloxPage.prototype._maskAmount.bind(this),
                    default: 0,
                }),
            },
            view: {
                list: new fields.element(),
                grid: new fields.element(),
                form: new fields.element(),
            },
            item: new fields.element({
                events: [['click', this._onClickItem]],
            }),
        };
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);
            this._parseAds();
            framework.hideLoading();
        });
    },

    _parseAds: function () {
        $('[field="ad.item"][data-value]').each((i, e) => {
            const $this = $(e);
            this.values.ads[e.dataset.id] = {
                id: $this.data('id'),
                img: $this.find('.escrow-ad-item-image img').attr('src'),
                name: $this.find('.escrow-ad-item-name').text().trim(),
                categ: $this.find('.escrow-ad-item-categ').text().trim(),
                price: $this.find('.escrow-ad-item-price').text().trim(),
                state: $this.find('.escrow-ad-item-state').html().trim(),
                desc: $this.find('.escrow-ad-item-desc').html().trim(),
            };
        });
    },

    _onClickButtonSidebarToggle: function (ev) {
        $('.escrow-ad-wrapper').toggleClass('blur');
        $('.escrow-ad-sidebar-section').addClass('d-none');
        this.ad.sideback.$.toggleClass('d-none');
        this.ad.sidebar.$.toggleClass('show');

        const value = ev?.currentTarget?.dataset?.value;
        if (value) {
            $(`.escrow-ad-sidebar-${value}`).removeClass('d-none');
        }
    },

    _onClickSideback: function () {
        this._onClickButtonSidebarToggle();
    },

    
    _activateView: function (view) {
        if (!this.ad.button[view].$.hasClass('active')) {
            for (const v of ['form', 'grid', 'list']) {
                if (this.ad.button[v].$.hasClass('active')) {
                    this.ad.button[v].$.removeClass('active');
                    this.ad.view[v].$.fadeOut(400, () => {
                        this.ad.view[view].$.fadeIn(400);
                    });
                }
            }
            this.ad.button[view].$.addClass('active');

            if (view === 'form') {
                $('.escrow-ad-read').fadeOut(400, () => {
                    $('.escrow-ad-edit').fadeIn(400);
                });
            } else {
                $('.escrow-ad-edit').fadeOut(400, () => {
                    $('.escrow-ad-read').fadeIn(400);
                });
            }
        }
    },

    _onClickButtonList: function () {
        this._activateView('list');
    },

    _onClickButtonGrid: function () {
        this._activateView('grid');
    },

    _onClickButtonForm: function () {
        this._activateView('form');
    },

    _onClickButtonDiscard: function () {
        this._activateView('list');
    },

    _onClickItem: function (ev) {
        this._onClickButtonSidebarToggle({ currentTarget: { dataset: { value: 'items'}}});

        const id = ev?.currentTarget?.dataset?.id;
        const value = this.values.ads[id];
        const $item = $('.escrow-ad-sidebar-items');
        if ($item.length) {
            $item.find('.escrow-ad-item-img').attr('src', value.img);
            $item.find('.escrow-ad-item-name').text(value.name);
            $item.find('.escrow-ad-item-categ').text(value.categ);
            $item.find('.escrow-ad-item-price').text(value.price);
            $item.find('.escrow-ad-item-state').html(value.state);
            $item.find('.escrow-ad-item-desc').html(value.desc);
        } else {
            $item.find('.escrow-ad-item-img').attr('src', '/web/image/product.product/0/logo');
            $item.find('.escrow-ad-item-name').text(_('No ad found'));
            $item.find('.escrow-ad-item-categ').text('');
            $item.find('.escrow-ad-item-price').text('');
            $item.find('.escrow-ad-item-state').html('');
            $item.find('.escrow-ad-item-desc').html('');
        }
    },

});
