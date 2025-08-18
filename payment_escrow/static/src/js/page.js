/** @odoo-module alias=paylox.system.escrow **/
'use strict';

import rpc from 'web.rpc';
import core from 'web.core';
import publicWidget from 'web.public.widget';
import framework from 'paylox.framework';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';
import { format } from 'paylox.tools';

const _t = core._t;

publicWidget.registry.payloxSystemEscrow = publicWidget.Widget.extend({
    selector: '.payment-escrow #wrapwrap',
    jsLibs: [
        '/payment_jetcheckout/static/src/lib/imask/imask.js',
        '/payment_jetcheckout/static/src/lib/filepond/filepond.js',
    ],

    init: function (parent, options) {
        this._super(parent, options);
        this.values = {
            ads: {},
        };
        this.state = {
            id: 0,
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
                edit: new fields.element({
                    events: [['click', this._onClickButtonEdit]],
                }),
                save: new fields.element({
                    events: [['click', this._onClickButtonSave]],
                }),
            },
            input: {
                img: new fields.file({
                    allowMultiple: false,
                    accept: 'image/*',
                    maxFileSize: '5MB',
                }),
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
                events: [['click', this._onClickAd]],
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
            const categ = $this.find('.escrow-ad-item-categ');
            this.values.ads[e.dataset.id] = {
                id: $this.data('id'),
                img: $this.find('.escrow-ad-item-image img').attr('src'),
                name: $this.find('.escrow-ad-item-name').text().trim(),
                categ: { id: categ.data('id'), name: categ.text().trim() },
                price: parseFloat($this.find('.escrow-ad-item-price').data('value')),
                state: $this.find('.escrow-ad-item-state').html().trim(),
                desc: $this.find('.escrow-ad-item-desc').html().trim(),
            };
        });
    },

    _updateAds: function (value) {
        const $items = this.ad.item.$.filter(`[data-id=${value.id}]`);
        console.log(this.ad.item.$);
        console.log($items);
        this.values.ads[value.id]['name'] = value.name;
        if ($items.length) {
            $items.find('[name=name]').text(value.name);
        }
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

    _onClickButtonEdit: function (ev) {
        this._prepareAd($(ev.currentTarget).data('id'));
        this._activateView('form');
        this._onClickSideback();
    },

    _onClickButtonSave: function (ev) {
        framework.showLoading();
        let params = {
            id: this.state.id,
            name: this.ad.input.name.value,
            categ: this.ad.input.categ.value,
            price: this.ad.input.price.value,
            desc: this.ad.input.desc.value,
            img: this.ad.input.img.value,
        }
        rpc.query({ route: '/my/ad/save', params }).then((result) => {
            if ('error' in result) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('An error occured.') + ' ' + result.error,
                });
            } else {
                params.id = result.id;
                this._updateAds(params);
                this._activateView('list');
                this.displayNotification({
                    type: 'success',
                    title: _t('Success'),
                    message: this.state.id ? _t('Ad has been added.') : _t('Ad has been saved.'),
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
    },

    _onClickAd: function (ev) {
        this._onClickButtonSidebarToggle({ currentTarget: { dataset: { value: 'items'}}});

        const id = ev?.currentTarget?.dataset?.id;
        const value = this.values.ads[id];
        const $item = $('.escrow-ad-sidebar-items');
        if ($item.length) {
            $item.find('.escrow-ad-item-img').attr('src', value.img);
            $item.find('.escrow-ad-item-name').text(value.name);
            $item.find('.escrow-ad-item-categ').text(value.categ.name);
            $item.find('.escrow-ad-item-price').text(format.currency(value.price, this.currency.position, this.currency.symbol, this.currency.decimal));
            $item.find('.escrow-ad-item-state').html(value.state);
            $item.find('.escrow-ad-item-desc').html(value.desc);
            $item.find('.escrow-ad-button-edit').data('id', id);
        } else {
            $item.find('.escrow-ad-item-img').attr('src', '/payment_jetcheckout/static/src/img/placeholder.png');
            $item.find('.escrow-ad-item-name').text(_('No ad found'));
            $item.find('.escrow-ad-item-categ').text('');
            $item.find('.escrow-ad-item-price').text('');
            $item.find('.escrow-ad-item-state').html('');
            $item.find('.escrow-ad-item-desc').html('');
            $item.find('.escrow-ad-button-edit').data('id', 0);
        }
    },

    _prepareAd: function (id) {
        this.state.id = parseInt(id);
        const ad = this.values.ads[id];
        this.ad.input.name.value = ad.name;
        this.ad.input.categ.value = ad.categ.id;
        this.ad.input.price.value = format.float(ad.price);
        this.ad.input.desc.value = ad.desc;
        setTimeout(() => this.ad.input.img.value = ad.img, 1000);
    },

});
