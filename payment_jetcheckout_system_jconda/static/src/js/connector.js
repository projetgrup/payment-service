odoo.define('payment_jetcheckout_system_jconda.payment_page', function (require) {
"use strict";

var core = require('web.core');
var publicWidget = require('web.public.widget');
var rpc = require('web.rpc');
var dialog = require('web.Dialog');
var paymentSystemPage = publicWidget.registry.JetcheckoutPaymentSystemPage;

var qweb = core.qweb;
var _t = core._t;

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
        rpc.query({route: '/my/payment/partners'}).then(function (partners) {
            const popup = new dialog(this, {
                title: _t('Select a partner'),
                $content: qweb.render('payment_jetcheckout_system_jconda.partner_list', {partners: partners}),
                dialogClass: 'o_connector_table_partner'
            })
            popup.opened(function() {
                $('.o_connector_search_partner').on('click', function(e) {
                    const query = $('.o_connector_query_partner').val();
                    let filtered;
                    if (query) {
                        let regex = new RegExp(query, 'i');
                        filtered = partners.filter((p) => p.company_name.match(regex));
                    } else {
                        filtered = partners;
                    }
                    const render = qweb.render('payment_jetcheckout_system_jconda.partner_list_line', {partners: filtered});
                    $('.o_connector_table_partner tbody').html(render);
                });
                $('.o_connector_select_partner').on('click', function(e) {
                    const $el = $(e.currentTarget);
                    rpc.query({
                        route: '/my/payment/partners/select',
                        params: {
                            vat: $el.data('vat'),
                            company: $el.data('company'),
                        },
                    }).then(function (result) {
                        $('label[for="partner"] + span').text($el.data('company'));
                        $('.o_connector_balance').html(result.render);
                        $('.o_connector_reset_partner').prop({'disabled': false}).removeClass('d-none').removeClass('disabled');
                        popup.destroy();
                    });
                });
            });
            popup.open();
        });
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