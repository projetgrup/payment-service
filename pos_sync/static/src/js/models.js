odoo.define('pos_sync.models', function (require) {
'use strict';

const exports = require('point_of_sale.models');
const { posbus } = require('point_of_sale.utils');

const PosModel = exports.PosModel.prototype;
exports.PosModel = exports.PosModel.extend({
    initialize: function () {
        PosModel.initialize.apply(this, arguments);
        this.sync_date = null;
        this.sync_on = false;
        this.sync_ok = false;
        this.sync_concurrent = false;
        this.sync_interval = 5000;

        const self = this;
        this.ready.then(function () {
            self.sync_ok = self.config.sync_ok;
            if (self.sync_ok) {
                self.sync_concurrent = self.config.sync_concurrent;
                self.sync_interval = Number.isInteger(self.config.sync_interval)  ? self.config.sync_interval * 1000 : 5000;
                if (self.sync_concurrent) {
                    const busService = self.env.services.bus_service;
                    busService.updateOption('pos', true);
                    busService.onNotification(self, self._process_bus);
                    busService.startPolling();
                }
                self.sync_orders();
            }
        });
    },

    _process_bus: function (datas) {
        for (let i=0; i < datas.length; i++) {
            this._process_sync(datas[i]['payload']);
        }
    },

    _clear_sync: function () {
        clearTimeout(this.sync_on);
        this.sync_on = false;
    },

    _get_sync_orders: function () {
        return this.get_order_list().filter(order => order.is_syncing() && !order.is_synced());
    },

    _process_sync: function (data) {
        if (data.type === 'order' && data.session == this.pos_session.id && data.cashier != this.pos_session.login_number) {
            this._process_sync_orders(data);
        }
    },

    _process_sync_orders: function (data) {
        this._clear_sync();
        this.sync_date = data.date;

        const orders = this._get_sync_orders();
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
                var employee;
                if (json.employee_id) {
                    employee = self.employees.find(e => e.id === json.employee_id);
                } else {
                    employee = self.users.find(u => u.id === json.user_id);
                }

                if (currentOrder) {
                    json.is_owner = currentOrder.is_owner;
                    currentOrder.pause_syncing();
                    currentOrder.paymentlines.remove(currentOrder.paymentlines.models);
                    currentOrder.orderlines.remove(currentOrder.orderlines.models);
                    currentOrder.init_from_JSON(json);
                    currentOrder.employee = {name: employee.name, user_id: [employee.id, employee.name], role: employee.role, id: null, barcode: null,  pin: null};
                    currentOrder.set_synced();
                    currentOrder.continue_syncing();
                } else {
                    json.is_owner = false;
                    var newOrder = new exports.Order({}, { pos: self, json: json });
                    self.get('orders').add(newOrder);
                    newOrder.employee = {name: employee.name, user_id: [employee.id, employee.name], role: employee.role, id: null, barcode: null,  pin: null};
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

    _sync_orders: async function(orders) {
        const self = this;
        await this.rpc({
            route: '/pos/sync',
            params: {
                type: 'order',
                concurrent: this.sync_concurrent,
                id: this.pos_session.login_number,
                sid: this.pos_session.id,
                uid: this.session.uid,
                date: this.sync_date,
                orders: orders,
            }
        }, {timeout: 4500}).then(function (data) {
            self._process_sync(data);
        }).catch(function(error) {
            console.error(error);
        });
    },

    sync_orders: async function() {
        const self = this;
        if (this.sync_interval) {
            setInterval(async function () {
                try {
                    var orders = [];
                    self._get_sync_orders().forEach(function (order) {
                        orders.push({
                            name: order.uid,
                            data: JSON.stringify(order.export_as_JSON()),
                        });
                    });
    
                    if (!self.sync_concurrent || orders.length) {
                        self._sync_orders(orders);
                    }
                } catch (error) {
                    console.error(error);
                }
            }, self.sync_interval);
        } else {
            console.log('Zero interval synchronization can only be processed in concurrent mode.');
        }
    },

    set_cashier: function(employee) {
        const order = this.get_order();
        if (order && order.is_syncing() && !order.is_owner) {
            return;
        }
        PosModel.set_cashier.apply(this, arguments);
    },
});

const Order = exports.Order.prototype;
exports.Order = exports.Order.extend({
    initialize: function(attributes, options) {
        this.set({ syncing: false,  synced: true });
        this.pos_uid = options.pos.pos_session.login_number;
        this.is_owner = true;
        Order.initialize.apply(this, arguments);
    },

    init_from_JSON: function(json) {
        Order.init_from_JSON.apply(this, arguments);
        this.pos_uid = json.pos_uid;
        this.is_owner = json.is_owner;
    },

    export_as_JSON: function () {
        var json = Order.export_as_JSON.apply(this, arguments);
        json.pos_uid = this.pos_uid;
        json.is_owner = this.is_owner;
        if (!json.is_owner && this.user_id) {
            json.user_id = this.user_id;
        }
        return json;
    },

    save_to_db: function() {
        Order.save_to_db.apply(this, arguments);
        this.need_synced();

        if (!this.pos.sync_interval && !this.pos.sync_on && this.is_syncing() && !this.is_synced()) {
            const self = this;
            this.pos.sync_on = setTimeout(function() {
                self.pos._sync_orders([{
                    name: self.uid,
                    data: JSON.stringify(self.export_as_JSON()),
                }]);
            }, 500);
        }
    },

    clear_syncing: function () {
        clearTimeout(this.pos.sync_on);
        this.pos.sync_on = false;
    },

    is_syncing: function () {
        return this.get('syncing');
    },

    pause_syncing: function () {
        this.set('syncing', false, {silent: true});
    },

    continue_syncing: function () {
        this.set('syncing', true, {silent: true});
    },

    stop_syncing: async function () {
        this.clear_syncing();
        this.set('syncing', false, {silent: true});
        if (this.pos.sync_ok) {
            try {
                await this.pos.rpc({
                    route: '/pos/sync',
                    params: {
                        type: 'order',
                        concurrent: this.pos.sync_concurrent,
                        id: this.pos.pos_session.login_number,
                        sid: this.pos.pos_session.id,
                        uid: this.pos.session.uid,
                        date: this.pos.sync_date,
                        orders: [{
                            name: this.uid,
                            data: false,
                        }],
                    }
                }, {timeout: 4500});
            } catch (error) {
                console.error(error);
            }
        }
    },

    start_syncing: function () {
        this.set('syncing', true, {silent: true});
        this.save_to_db();
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
});
});