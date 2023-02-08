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

const core = require('web.core');
const KanbanController = require('web.KanbanController');
const qweb = core.qweb;

const DashboardController = KanbanController.extend({
    events: _.extend({
        'click .o_button_payment_page': '_onClickPaymentPage'
    }, KanbanController.prototype.events),

    renderButtons: function () {
        this.$buttons = $(qweb.render('Dasboard.Buttons'));
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
    