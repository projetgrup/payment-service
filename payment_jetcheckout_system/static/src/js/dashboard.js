odoo.define('payment_jetcheckout_system.DashboardView', function (require) {
"use strict";

const DashboardController = require('payment_jetcheckout_system.DashboardController');
const KanbanView = require('web.KanbanView');
const viewRegistry = require('web.view_registry');

const DasboardView = KanbanView.extend({
    config: _.extend({}, KanbanView.prototype.config, {
        Controller: DashboardController
    })
});

viewRegistry.add('account_dashboard_kanban', DasboardView);
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
        var self = this;
        var ready = this._rpc({
            model: 'payment.acquirer',
            method: 'has_dashboard_button',
            args: [],
        }).then(function (shown) {
            self.dashboard_button_shown = shown;
        }).guardedCatch(function (error) {
            console.error(error);
        });
        return Promise.all([this._super.apply(this, arguments), ready]);
    },

    renderButtons: function () {
        if (this.dashboard_button_shown) {
            this.$buttons = $(qweb.render('Dashboard.Buttons'));
        }
    },

    _onClickPaymentPage: function () {
        this.do_action({
            type: 'ir.actions.act_url',
            target: 'new',
            url: '/my/payment',
        });
    },
});

return DashboardController;
});
    