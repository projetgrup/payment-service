/** @odoo-module alias=paylox.system.jewelry.register **/
'use strict';

import publicWidget from 'web.public.widget';
import core from 'web.core';
import rpc from 'web.rpc';

const _t = core._t;
const Qweb = core.qweb;

publicWidget.registry.payloxSystemJewelryRegister = publicWidget.Widget.extend({
    selector: '.payment-jewelry-register #wrapwrap',
    xmlDependencies: ['/payment_jewelry/static/src/xml/register.xml'],
    events: {
        'click button.search': '_onClickSearch',
    },

    _onClickSearch: function () {
        let $vat = $('#vat');
        let $result = $('.result');
        let $info = $result.find('.info');
        let $loading = $result.find('.loading');

        $result.addClass('show');
        $loading.addClass('show');
        rpc.query({
            route: '/my/jewelry/register/query',
            params: { vat: $vat.val() }
        }).then((result) => {
            if (result.error) {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
            }
            $info.html(Qweb.render('paylox.jewelry.register', result));
            $loading.removeClass('show');
        }).guardedCatch(() => {
            this.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please contact with your system administrator.'),
            });
            $info.html(Qweb.render('paylox.jewelry.register', values));
            $loading.removeClass('show');
        });
    },
});