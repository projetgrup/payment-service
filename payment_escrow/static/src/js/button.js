odoo.define('payment_escrow.BrandController', function (require) {
const ListController = require('web.ListController');
const BrandController = ListController.extend();
return BrandController;
});

odoo.define('payment_escrow.BrandList', function (require) {
'use strict';

const BrandController = require('payment_escrow.BrandController');
const viewRegistry = require('web.view_registry');
const ListView = require('web.ListView');
const core = require('web.core');

const BrandListController = BrandController.extend({
    events: _.extend({}, BrandController.prototype.events, {
        'click .o_button_sync_brand': '_onClickImportBrand',
    }),

    willStart: function() {
        const ready = this.getSession().user_has_group('payment_escrow.group_escrow_manager').then((is_admin) => {
            if (is_admin) {
                this.buttons_template = 'BrandListView.buttons';
            }
        });
        return Promise.all([this._super.apply(this, arguments), ready]);
    },

    _onClickImportBrand: function () {
        return this.do_action('payment_escrow.action_sync', {
            on_close: this.reload.bind(this, {}),
            additional_context: {
                ...this.controlPanelProps.action.context,
                active_model: this.controlPanelProps.action.res_model,
                active_line: 'brand'
            },
        });
    }
});

const BrandListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: BrandListController,
    }),
});

viewRegistry.add('brand_buttons', BrandListView);
});

