odoo.define('payment_jetcheckout_system.DashboardController', function (require) {
"use strict";

const DashboardController = require('payment_jetcheckout.DashboardController');

DashboardController.include({
    _getUrl: function () {
        return '/my/payment';
    },
});

return DashboardController;
});
