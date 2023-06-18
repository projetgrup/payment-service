odoo.define('payment_jetcheckout.widget', function (require) {
'use strict';

const { FormViewDialog } = require('web.view_dialogs');
const core = require('web.core');

FormViewDialog.include({
    init: function (parent, options) {
        if (options && options.context && options.context.no_edit) {
            options.readonly = true;
        }
        this._super(parent, options);
    },
});

function redirectAcquirer(parent, action) {
    let {back=false, next=false} = action.params || {};
    if (back) {
        $('.breadcrumb-item.o_back_button').trigger('click');
    }
    return next;
}
core.action_registry.add("redirect_acquirer", redirectAcquirer);
});
