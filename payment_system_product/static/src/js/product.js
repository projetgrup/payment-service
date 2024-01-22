odoo.define('payment_system_product.ProductView', function (require) {
"use strict";

const KanbanController = require('web.KanbanController');
const ListController = require('web.ListController');
const KanbanView = require('web.KanbanView');
const ListView = require('web.ListView');
const viewRegistry = require('web.view_registry');
const { qweb, _t } = require('web.core');

const View = (view, controller) => {
    return view.extend({
        config: _.extend({}, view.prototype.config, {
            Controller: controller.extend({
                events: _.extend({
                    'click .o_button_update_price': '_onClickUpdatePrice',
                }, controller.prototype.events),

                willStart: function() {
                    let ready = this._rpc({
                        model: 'payment.product',
                        method: 'show_buttons',
                        args: [],
                    }).then(({ show_update_price_button }) => {
                        this.show_update_price_button = show_update_price_button;
                    }).guardedCatch((error) => {
                        console.error(error);
                    });
                    return Promise.all([this._super.apply(this, arguments), ready]);
                },

                renderButtons: function () {
                    this._super.apply(this, arguments);
                    let $buttons = $(qweb.render('Payment.Product.Buttons', {
                        show_update_price_button: this.show_update_price_button,
                    }));
                    if (this.$buttons) {
                        let $export = this.$buttons.find('.o_list_export_xlsx');
                        if ($export.length) {
                            $export.before($buttons);
                        } else {
                            this.$buttons.append($buttons);
                        }
                    } else {
                        this.$buttons = $buttons;
                    }
                },

                _onClickUpdatePrice: function () {
                    this._rpc({
                        model: 'payment.product',
                        method: 'update_price',
                        args: [],
                    }).then((res) => {
                        if (res.error) {
                            this.displayNotification({
                                type: 'danger',
                                title: _t('Error'),
                                message: _t('An error occured.'),
                            });
                        } else {
                            this.displayNotification({
                                type: 'info',
                                title: _t('Success'),
                                message: _t('Prices have been updated.'),
                            });
                            this.reload();
                        }
                    }).guardedCatch((error) => {
                        this.displayNotification({
                            type: 'danger',
                            title: _t('Error'),
                            message: _t('An error occured.'),
                        });
                    });
                },
            }),
        }),
    });
}

viewRegistry.add('payment_system_product_kanban', View(KanbanView, KanbanController));
viewRegistry.add('payment_system_product_list', View(ListView, ListController));
});