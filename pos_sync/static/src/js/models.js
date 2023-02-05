odoo.define('pos_sync.models', function (require) {
'use strict';

const exports = require('point_of_sale.models');
const { posbus } = require('point_of_sale.utils');

const PosModel = exports.PosModel.prototype;
exports.PosModel = exports.PosModel.extend({
    initialize: function () {
        PosModel.initialize.apply(this, arguments);
        this.sync_date = null;
        this.sync_continuous = false;
        this.sync_latency = 5000;

        const self = this;
        this.ready.then(function () {
            self.sync_continuous = self.config.sync_continuous;
            self.sync_latency = self.config.sync_latency ? self.config.sync_latency * 1000 : 5000;
            if (self.sync_continuous) {
                const busService = self.env.services.bus_service;
                busService.updateOption('pos', true);
                busService.onNotification(self, self._process_bus);
                busService.startPolling();
            }
        });
    },

    _process_bus: function (data) {
        for (let i=0; i < data.length; i++) {
            this._process_sync(data[i]['payload']);
        }
    },

    _get_sync: function () {
        return this.get_order_list().filter(order => order.is_syncing() && !order.is_synced());
    },

    _process_sync: function (data) {
        this.sync_date = data.date;
        const orders = this._get_sync();
        orders.forEach(function (order) {
            order.set_synced();
        });

        if (_.isEmpty(data)) {
            return;
        }

        const self = this;
        data.orders.forEach(function (order) {
            var json = JSON.parse(order.data);
            var currentOrder = self.get_order_list().find(o => o.uid === order.name);
            if (order.data) {
                var user = self.users.find(u => u.id === json.user_id);
                if (currentOrder) {
                    currentOrder.paymentlines.forEach(function (line) {
                        currentOrder.remove_paymentline(line);
                    });

                    currentOrder.orderlines.forEach(function (line) {
                        currentOrder.remove_orderline(line);
                    });

                    currentOrder.init_from_JSON(json);
                    currentOrder.employee = {name: user.name, user_id: [user.id, user.name], role: user.role, id: null, barcode: null,  pin: null};
                    currentOrder.start_syncing();
                    currentOrder.set_synced();
                } else {
                    var newOrder = new exports.Order({}, { pos: self, json: json });
                    self.get('orders').add(newOrder);
                    newOrder.employee = {name: user.name, user_id: [user.id, user.name], role: user.role, id: null, barcode: null,  pin: null};
                    newOrder.start_syncing();
                    newOrder.set_synced();
                }
                posbus.trigger('order-deleted');
            } else {
                if (currentOrder) {
                    const selectedOrder = self.get_order();
                    const currentOrderOn = selectedOrder && selectedOrder.uid === currentOrder.uid;
                    currentOrder.destroy({ reason: 'abandon' });
                    posbus.trigger('order-deleted');
                    if (currentOrderOn) {
                        posbus.trigger('synced-order-completed');
                    }
                }
            }
        });
    },

    load_orders: async function(){
        await PosModel.load_orders.apply(this, arguments);
        this.sync_orders();
    },

    sync_orders: async function() {
        const self = this;
        setInterval(async function () {
            try {
                var orders = [];
                self._get_sync().forEach(function (order) {
                    orders.push({
                        name: order.uid,
                        data: JSON.stringify(order.export_as_JSON()),
                    });
                });

                if (!self.sync_continuous || orders.length) {
                    await self.rpc({
                        route: '/pos/sync',
                        params: {
                            id: self.pos_session.login_number,
                            sid: self.pos_session.id,
                            uid: self.session.uid,
                            date: self.sync_date,
                            orders: orders,
                            polling: self.sync_continuous,
                        }
                    }, {timeout: 4500}).then(function (data) {
                        self._process_sync(data);
                    }).catch(function(error) {
                        console.error(error);
                    });
                }
            } catch (error) {
                console.error(error);
            }
        }, self.sync_latency);
    },
});

const Order = exports.Order.prototype;
exports.Order = exports.Order.extend({
    initialize: function() {
        this.set({ syncing: false,  synced: true });
        Order.initialize.apply(this, arguments);
    },

    export_as_JSON: function () {
        var json = Order.export_as_JSON.apply(this, arguments);
        json.is_owner = this.is_owner();
        if (!json.is_owner && this.user_id) {
            json.user_id = this.user_id;
        }
        return json;
    },

    save_to_db: function() {
        Order.save_to_db.apply(this, arguments);
        this.need_synced();
    },

    is_syncing: function () {
        return this.get('syncing');
    },

    stop_syncing: async function () {
        this.set('syncing', false, {silent: true});
        try {
            await this.pos.rpc({
                route: '/pos/sync',
                params: {
                    action: 'done',
                    name: this.uid,
                }
            }, {timeout: 4500});
        } catch (error) {
            console.log(error);
        }
    },

    start_syncing: function () {
        this.set('syncing', true, {silent: true});
    },

    need_synced: function () {
        this.set('synced', false, {silent: true});
    },

    set_synced: function () {
        this.set('synced', true, {silent: true});
    },

    is_synced: function () {
        return this.get('synced');
    },

    is_owner: function () {
        return this.employee.user_id[0] === this.pos.user.id;
    },
});
});