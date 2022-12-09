odoo.define('payment_jetcheckout_system_jconda.payment_page', function (require) {
"use strict";

let core = require('web.core');
let publicWidget = require('web.public.widget');
let rpc = require('web.rpc');
let dialog = require('web.Dialog');
let paymentSystemPage = publicWidget.registry.JetcheckoutPaymentSystemPage;

let qweb = core.qweb;
let _t = core._t;
let pageSize = 2;

paymentSystemPage.include({
    events: _.extend({}, paymentSystemPage.prototype.events, {
        'click .o_connector_get_partner': '_onClickConnectorGetPartner',
        'click .o_connector_reset_partner': '_onClickConnectorResetPartner',
    }),

    xmlDependencies: (paymentSystemPage.prototype.xmlDependencies || []).concat(
        ["/payment_jetcheckout_system_jconda/static/src/xml/connector.xml"]
    ),

    _onClickConnectorGetPartner: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const self = this;
        rpc.query({route: '/my/payment/partners'}).then(function (partners) {
            const pages = self._onClickConnectorPagePartner(partners);
            const popup = new dialog(this, {
                title: _t('Select a partner'),
                $content: qweb.render('payment_jetcheckout_system_jconda.partner_list', {partners: partners.slice(0, pageSize), pages: pages}),
                dialogClass: 'o_connector_table_partner'
            });
            popup.opened(function() {
                $('.o_connector_search_partner').click(function(e) { self._onClickConnectorSearchPartner(partners); });
                $('.o_connector_query_partner').keypress(function(e) { if (e.key === 'Enter') self._onClickConnectorSearchPartner(partners); });
                $('.o_connector_select_partner').click(function(e) {
                    const $el = $(e.currentTarget);
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
                        $('.o_connector_reset_partner').prop({'disabled': false}).removeClass('d-none').removeClass('disabled');
                        popup.destroy();
                    }).guardedCatch(function () {
                        popup.destroy();
                    });
                });
            });
            popup.open();
        });
    },

    _onClickConnectorSearchPartner: function (partners) {
        const pages = self._onClickConnectorPagePartner(partners);
        const query = $('.o_connector_query_partner').val();
        let filtered;
        if (query) {
            let regex = new RegExp(query, 'i');
            filtered = partners.filter((p) => p.company_name.match(regex));
        } else {
            filtered = partners;
        }
        const render = qweb.render('payment_jetcheckout_system_jconda.partner_list_line', {partners: filtered.slice(0, pageSize)});
        $('.o_connector_table_partner tbody').html(render);
    },

    _onClickConnectorPagePartner: function (partners) {
        const total = Math.ceil(partners.length / pageSize);
        const firstPages = [];
        const lastPages = [];
        for(let i=1;i<=5;i++) {
            firstPages.push(i);
            if (total === i) {
                break;
            }
        }
        if (total > 5) {
            for(let i=1;i<=3;i++) {
                if (total === 5) {
                    firstPages.push(0);
                    break;
                }
                lastPages.unshift(total);
                total--;
            }
        }
        return firstPages.concat(lastPages);
    },

    _onClickConnectorResetPartner: function (ev) {
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