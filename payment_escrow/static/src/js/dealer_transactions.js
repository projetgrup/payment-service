/** @odoo-module alias=paylox.system.escrow.dealer.transaction **/
'use strict';

import rpc from 'web.rpc';
import { _t } from 'web.core';
import publicWidget from 'web.public.widget';
import payloxPage from 'paylox.page';
import framework from 'paylox.framework';
import fields from 'paylox.fields';


publicWidget.registry.payloxDealerTransaction = payloxPage.extend({
    selector: '.dealer-transactions #wrapwrap',
    jsLibs: [
        '/payment_jetcheckout/static/src/lib/imask/imask.js',
        '/payment_jetcheckout/static/src/lib/filepond/filepond.js',
    ],

    init: function (parent, options) {
        this._super(parent, options);
        this.transaction = {
            button : {
                showBrokerDetails: new fields.element({
                    events: [['click', this._onShowBrokerDetails]]
                }),
                showTransactionDetails: new fields.element({
                    events: [['click', this._onShowTransactionDetails]]
                })
            },
            transactionSection: new fields.element(),
            brokerSection: new fields.element(),
        }
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);
            this._initBrokerFilter();
            framework.hideLoading();
            console.log('Dealer Transactions page loaded');
            setTimeout(() => $('div.o_loading').addClass('transparent'), 2000);
        });
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Initialize broker filter functionality
     * @private
     */
    _initBrokerFilter: function() {
        const self = this;
        $('.filter-btn').on('click', function(e) {
            e.preventDefault();
            
            // Update active state
            $('.filter-btn').removeClass('active');
            $(this).addClass('active');
            
            const brokerId = $(this).data('broker');
            
            // Show/hide transactions based on broker filter
            if (brokerId === 'all') {
                $('.escrow-ad-list-item').fadeIn(300);
            } else {
                $('.escrow-ad-list-item').each(function() {
                    const itemBrokerId = $(this).data('broker-id');
                    if (itemBrokerId == brokerId) {
                        $(this).fadeIn(300);
                    } else {
                        $(this).fadeOut(300);
                    }
                });
            }
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Show broker details handler
     * @private
     * @param {Event} ev
     */
    _onShowBrokerDetails: function(ev) {
        ev.preventDefault();
        console.log('show broker details');
        
        const $brokersSection = this.transaction.brokerSection.$;
        const $transactionsSection = this.transaction.transactionSection.$;
        const $cards = $('.view-toggle-card');

        $cards.removeClass('active-card');
        $(ev.currentTarget).addClass('active-card');

        $transactionsSection.fadeOut(300, function() {
            $brokersSection.fadeIn(400);
        });
    },

    /**
     * Show transaction details handler
     * @private
     * @param {Event} ev
     */
    _onShowTransactionDetails: function(ev) {
        ev.preventDefault();
        console.log('show transaction details');
        
        const $brokersSection = this.transaction.brokerSection.$;
        const $transactionsSection = this.transaction.transactionSection.$;
        const $cards = $('.view-toggle-card');

        $cards.removeClass('active-card');
        $(ev.currentTarget).addClass('active-card');

        $brokersSection.fadeOut(300, function() {
            $transactionsSection.fadeIn(400);
        });
    },

});
