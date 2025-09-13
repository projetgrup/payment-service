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
        this.state = { id: 0, step: 0 };
    },
    
    _getParams: function() {
        const different = $('input[name=checkPoint]').is(':checked');
        const params = this._super.apply(this, arguments);
        this._getEscrowItems();
        params.system = 'escrow';
        params.products = [{'pid': this.state.id, 'qty': 1}];
        console.log(this.state);
        if (different) {
            const $card = $('.payment-info-card');
            params.different_holder = {
                vat : $card.find('[field="payment.different.info.display.tc"]').text(),
                different: true,
            };
        }
        return params;
    },

    _getEscrowItems: function () {
        let hash = new URLSearchParams(window.location.search).get('');
        if (hash) {
            try {
                let state = JSON.parse(atob(hash));
                Object.assign(this.state, {
                    id: state.i,
                    step: state.s,
                });
            } catch {
                window.history.replaceState(null, '', window.location.pathname);
            }
        }
    },

    _getEscrowFiles: function () {
        const $el = $('input[name=fileConveyance]');
        if ($el.length) {
            let file = JSON.parse($el);
            return [{
                type: 'conveyance',
                name: file.name,
                data: file.data,
                mimetype: file.type,
            }]
        }
        return [];
    },
});
