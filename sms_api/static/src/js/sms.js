/** @odoo-module **/

import smsWidget from '@sms/js/fields_sms_widget';

smsWidget.include({
    _renderEdit: function () {
        var self = this;
        var def = this._super.apply(this, arguments);
        this.$('.btn-credit').on('click', function(ev){
            ev.preventDefault();
            self._rpc({
                model: 'sms.api',
                method: 'get_credit',
                args: [],
            }).then(function (result) {
                self.displayNotification({
                    type: 'info',
                    message: result,
                    sticky: false,
                });
            });
        });
        return def;
    },
    _renderIAPButton: function () {
        return '<a class="fa fa-lg fa-info-circle btn-credit ml-2 text-primary" role="button" style="cursor: pointer"></a>';
    },
});
