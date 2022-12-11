odoo.define('payment_jetcheckout_system_jconda.payment_page', function (require) {
"use strict";

let core = require('web.core');
let publicWidget = require('web.public.widget');
let rpc = require('web.rpc');
let dialog = require('web.Dialog');
var framework = require('payment_jetcheckout.framework');
let paymentSystemPage = publicWidget.registry.JetcheckoutPaymentSystemPage;

let qweb = core.qweb;
let _t = core._t;
let pageSize = 5;

paymentSystemPage.include({
    events: _.extend({}, paymentSystemPage.prototype.events, {
        'click .o_connector_partner_get': '_onClickConnectorPartnerGet',
        'click .o_connector_partner_reset': '_onClickConnectorPartnerReset',
    }),

    xmlDependencies: (paymentSystemPage.prototype.xmlDependencies || []).concat(
        ["/payment_jetcheckout_system_jconda/static/src/xml/connector.xml"]
    ),

    init: function () {
        this._super.apply(this, arguments);
        this.connector = {
            partners: [],
            partner: [],
            filter: false,
            page: 1,
            getPartners: function () {
                return this.filter && this.partner || this.partners;
            }
        };
    },

    _onClickConnectorPartnerGet: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        framework.showLoading();
        if (!this.connector.partners.length) {
            const self = this;
            rpc.query({route: '/my/payment/partners'}).then(function (partners) {
                self._getConnectorPartners(partners);
            });
        } else {
            this._getConnectorPartners(this.connector.partners);
        }
    },

    _getConnectorPartners: function (partners) {
        this.connector.partners = partners;
        this.connector.partner = [];
        this.connector.filter = false;
        this.connector.page = 1;
        const self = this;
        const pages = this._getConnectorPartnerPages();
        const popup = new dialog(this, {
            title: _t('Select a partner'),
            $content: qweb.render('payment_jetcheckout_system_jconda.partner_list', {partners: partners.slice(0, pageSize), pages: pages, page: 1}),
            dialogClass: 'o_connector_partner_table'
        });
        popup.opened(function() {
            $('.o_connector_partner_pages').click(self._onClickConnectorPartnerPage.bind(self));
            $('.o_connector_partner_search').click(self._onClickConnectorPartnerSearch.bind(self));
            $('.o_connector_partner_query').keypress(self._onClickConnectorPartnerSearch.bind(self));
            $('.o_connector_partner_table tbody').click(function(ev) {
                const $el = $(ev.target);
                if ($el.prop('tagName') !== 'BUTTON') return;
                $('.o_connector_partner_select').prop({'disabled': 'disabled'}).addClass('disabled');
                rpc.query({
                    route: '/my/payment/partners/select',
                    params: {
                        vat: $el.data('vat'),
                        company: $el.data('company'),
                    },
                }).then(function (result) {
                    $el.prop({'disabled': 'disabled'}).addClass('disabled');
                    $('label[for="partner"] + span').text($el.data('company'));
                    $('.o_connector_balance').html(result.render);
                    $('.o_connector_partner_reset').prop({'disabled': false}).removeClass('d-none').removeClass('disabled');
                    popup.destroy();
                }).guardedCatch(function () {
                    popup.destroy();
                });
            });
        });
        popup.open();
        framework.hideLoading();
    },

    _onClickConnectorPartnerSearch: function (ev) {
        if (ev.key && ev.key !== 'Enter') return;
        const query = $('.o_connector_partner_query').val();
        var partners = this.connector.partners;
        if (query) {
            let regex = new RegExp(query, 'i');
            partners = partners.filter((p) => p.company_name.match(regex));
            this.connector.partner = partners;
            this.connector.filter = true;
            this.connector.page = 1;
        } else {
            this.connector.partner = [];
            this.connector.filter = false;
            this.connector.page = 1;
        }
        const render = qweb.render('payment_jetcheckout_system_jconda.partner_list_line', {partners: partners.slice(0, pageSize)});
        $('.o_connector_partner_table tbody').html(render);
        this._renderConnectorPartnerPages(1);
    },

    _onClickConnectorPartnerPage: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const $el = $(ev.target);
        if ($el.prop('tagName') !== 'BUTTON') return;
        const page = parseInt($el.data('page'));
        this.connector.page = page;
        this._renderConnectorPartnerPages(page);
    },

    _getConnectorPartnerPages: function () {
        const partners = this.connector.getPartners();
        const page = this.connector.page;
        const firstPages = [];
        const middlePages = [];
        const lastPages = [];

        let total = Math.ceil(partners.length / pageSize) || 1;
        let limit = total;
        let iterator = 0;

        for(let i=1; i<=3; i++) {
            firstPages.push(i);
            if (total === i) break;
        }

        for(let i=1; i<=3; i++) {
            if (limit === 1) break;
            lastPages.unshift(limit);
            limit--;
        }

        if (total > 6) {
            if (page < 4) {
                for(let i=4; i<=limit; i++) {
                    middlePages.push(i);
                    iterator++;
                    if (iterator === 3) break;
                }
            } else if (page > limit){
                for(let i=limit; i>=4; i--) {
                    middlePages.unshift(i);
                    iterator++;
                    if (iterator === 3) break;
                }
            } else {
                for(let i=-1; i<=1; i++) {
                    middlePages.push(page + i);
                }
            }

            if (middlePages[0] === 3) {
                middlePages.shift();
                if (!lastPages.includes(6)) middlePages.push(6);
            }
            if (middlePages.at(-1) === lastPages[0]) {
                middlePages.pop();
                if (!firstPages.includes(limit - 2)) middlePages.unshift(limit - 2);
            }

            if (middlePages[0] > 4) middlePages.unshift(0);
            if (middlePages.at(-1) < limit) middlePages.push(0);
        }

        return firstPages.concat(middlePages.concat(lastPages));
    },

    _renderConnectorPartnerPages: function (page=1) {
        const partners = this.connector.getPartners();
        const pages = this._getConnectorPartnerPages();

        const render_page = qweb.render('payment_jetcheckout_system_jconda.partner_list_page', {pages: pages, page: page});
        $('.o_connector_partner_pages').html(render_page);

        const firstLine = (page - 1) * pageSize;
        const render_list = qweb.render('payment_jetcheckout_system_jconda.partner_list_line', {partners: partners.slice(firstLine, firstLine + pageSize)});
        $('.o_connector_partner_table tbody').html(render_list);
    },

    _onClickConnectorPartnerReset: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const $el = $(ev.currentTarget);
        $el.prop({'disabled': 'disabled'}).addClass('disabled');
        rpc.query({
            route: '/my/payment/partners/reset',
        }).then(function (result) {
            if (!result) return false;
            $('label[for="partner"] + span').text(result.name);
            $('.o_connector_balance').html(result.render);
            $el.addClass('d-none');
        });
    },
});

});