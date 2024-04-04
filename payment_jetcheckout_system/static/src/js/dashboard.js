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
        'click button.o_button_dashboard': '_onClickButton',
    }, KanbanController.prototype.events),

    willStart: function() {
        const ready = this._rpc({
            model: 'payment.dashboard',
            method: 'has_payment_button',
            args: [],
        }).then(({ show_payment_button, show_contactless_button, show_preview_button }) => {
            this.show_payment_button = show_payment_button;
            this.show_contactless_button = show_contactless_button;
            this.show_preview_button = show_preview_button;
        }).guardedCatch((error) => {
            console.error(error);
        });
        return Promise.all([this._super.apply(this, arguments), ready]);
    },

    renderButtons: function () {
        this.$buttons = $(qweb.render('Dashboard.Buttons', {
            show_payment_button: this.show_payment_button,
            show_contactless_button: this.show_contactless_button,
            show_preview_button: this.show_preview_button,
        }));
    },

    _onClickButton: function (ev) {
        this._rpc({
            model: 'payment.dashboard',
            method: 'get_button_url',
            args: [ev.target.dataset.type],
        }).then((url) => {
            this.do_action({
                type: 'ir.actions.act_url',
                target: 'new',
                url: url,
            });
        }).guardedCatch((error) => {
            console.error(error);
        });
    },
});

return DashboardController;
});