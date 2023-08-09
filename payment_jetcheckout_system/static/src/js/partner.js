odoo.define('payment_jetcheckout_system.PartnerController', function (require) {
const ListController = require('web.ListController');
const PartnerController = ListController.extend();
return PartnerController;
});

odoo.define('payment_jetcheckout_system.PartnerView', function (require) {
const PartnerController = require('payment_jetcheckout_system.PartnerController');
const ListView = require('web.ListView');
const viewRegistry = require('web.view_registry');
const PartnerView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, { Controller: PartnerController })
});
viewRegistry.add('system_partner', PartnerView);
});