odoo.define('payment_jetcheckout_system.ItemController', function (require) {
const ListController = require('web.ListController');
const ItemController = ListController.extend();
return ItemController;
});

odoo.define('payment_jetcheckout_system.ItemView', function (require) {
const ItemController = require('payment_jetcheckout_system.ItemController');
const ListView = require('web.ListView');
const viewRegistry = require('web.view_registry');
const ItemView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, { Controller: ItemController })
});
viewRegistry.add('system_item', ItemView);
});