odoo.define('pos_sync.models', function (require) {
'use strict';

const exports = require('point_of_sale.models');

const PosModel = exports.PosModel.prototype;
exports.PosModel = exports.PosModel.extend({
    initialize: function() {
        PosModel.initialize.apply(this, arguments);
        this.sync_date = null;
    },

    load_orders: async function(){
        await PosModel.load_orders.apply(this, arguments);
        this.sync_orders();
    },

    sync_orders: async function() {
        var self = this;
        console.log(this);
        setInterval(async function () {
            try {
                var ordersList = self.get_order_list();
                var orderList = ordersList.filter(order => order.syncing && !order.is_synced());
                var orders = [];
                orderList.forEach(function (order) {
                    orders.push({
                        name: order.name,
                        data: JSON.stringify(order.export_as_JSON()),
                    });
                });

                await self.rpc({
                    route: '/pos/sync',
                    params: {
                        id: self.pos_session.login_number,
                        sid: self.pos_session.id,
                        uid: self.session.uid,
                        date: self.sync_date,
                        orders: orders,
                    }
                }, {timeout: 4500}).then(function (result) {
                    self.sync_date = result.date;
                    orderList.forEach(function (order) {
                        order.set_synced();
                    });
                    result.orders.forEach(function (order) {
                        var json = JSON.parse(order.data);
                        var nowOrder = ordersList.find(o => o.name === json.name);
                        if (nowOrder) {
                            console.log('aynı');
                            console.log(nowOrder);
                            nowOrder.init_from_JSON(json)
                            //nowOrder.set_client(newOrder.get_client());
                            //self.get('orders').reset([newOrder]);
                            //nowOrder.collection.reset([ordersList]);
                            //nowOrder.trigger('change', nowOrder);
                            nowOrder.set_synced();
                        } else {
                            console.log('değil');
                            var newOrder = new exports.Order({}, { pos: self, json: json });
                            self.get('orders').add(newOrder);
                        }
                    });
                    console.log(result);
                }).catch(function(error) {
                    console.error(error);
                });
            } catch (error) {
                console.error(error);
            }
        }, 5000);
    }
});

const Order = exports.Order.prototype;
exports.Order = exports.Order.extend({
    initialize: function() {
        this.syncing = false;
        this.set({ synced: true });
        Order.initialize.apply(this, arguments);
    },

    save_to_db: function() {
        Order.save_to_db.apply(this, arguments);
        this.need_synced();
    },

    need_synced: function () {
        this.set('synced', false, {silent: true});
    },

    set_synced: function () {
        this.set('synced', true, {silent: true});
    },

    is_synced: function () {
        return this.get('synced');
    }
});
});