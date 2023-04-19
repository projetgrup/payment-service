odoo.define('payment_jetcheckout.TransactionList', function (require) {
'use strict';

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');
var core = require('web.core');

var _t = core._t;

var TransactionListController = ListController.extend({
    events: _.extend({}, ListController.prototype.events, {
        'click .o_button_import_transaction': '_onClickImportTransaction',
    }),

    willStart: function() {
        var self = this;
        var ready = this.getSession().user_has_group('account.group_account_manager').then(function (is_admin) {
            if (is_admin) {
                self.buttons_template = 'TransactionListView.buttons';
            }
        });
        return Promise.all([this._super.apply(this, arguments), ready]);
    },

    _onClickImportTransaction: function () {
        var action = {
            type: 'ir.actions.act_window',
            res_model: 'payment.transaction.import',
            name: _t('Import Transaction'),
            view_mode: 'form',
            views:[[false, 'form']],
            target: 'new',
        };
        this.do_action(action);
    },
});

var TransactionListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: TransactionListController,
    }),
});

viewRegistry.add('transaction_buttons', TransactionListView);
});
