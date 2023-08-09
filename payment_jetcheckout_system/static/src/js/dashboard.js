odoo.define('payment_jetcheckout_system.DashboardView', function (require) {
"use strict";

const DashboardController = require('payment_jetcheckout_system.DashboardController');
const KanbanView = require('web.KanbanView');
const viewRegistry = require('web.view_registry');

const DashboardView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Controller: DashboardController
    })
});

viewRegistry.add('account_dashboard_kanban', DashboardView);
});


odoo.define('payment_jetcheckout_system.DashboardController', function (require) {
"use strict";

const KanbanController = require('web.KanbanController');
const core = require('web.core');

const qweb = core.qweb;

const DashboardController = KanbanController.extend({
    events: _.extend({
        'click .o_button_payment_page': '_onClickPaymentPage'
    }, KanbanController.prototype.events),

    willStart: function() {
        const self = this;
        const ready = this._rpc({
            model: 'payment.acquirer',
            method: 'has_dashboard_button',
            args: [],
        }).then(function (show) {
            self.show_button = show;
        }).guardedCatch(function (error) {
            console.error(error);
        });
        return Promise.all([this._super.apply(this, arguments), ready]);
    },

    renderButtons: function () {
        if (this.show_button) {
            this.$buttons = $(qweb.render('Dashboard.Buttons'));
        }
    },

    _onClickPaymentPage: function () {
        const self = this;
        this._rpc({
            model: 'payment.dashboard',
            method: 'get_url',
            args: [],
        }).then(function (url) {
            self.do_action({
                type: 'ir.actions.act_url',
                target: 'new',
                url: url + '/my/payment',
            });
        }).guardedCatch(function (error) {
            console.error(error);
        });
    },
});

return DashboardController;
});
    