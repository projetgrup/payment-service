odoo.define('payment_jetcheckout.framework', function (require) {
"use strict";

function showLoading() {
    const $buttons = $('.payment_pay');
    const $loading = $('.o_payment_loading');
    if ($buttons.length) {
        $buttons.addClass('disabled');
        $buttons.prop('disabled', 'disabled');
    }
    if ($loading.length) {
        $loading.css('opacity', 1).css('visibility', 'visible');
    }
}

function hideLoading() {
    const $buttons = $('.payment_pay');
    const $loading = $('.o_payment_loading');
    if ($buttons.length) {
        $buttons.removeClass('disabled');
        $buttons.prop('disabled', false);
    }
    if ($loading.length) {
        $loading.css('opacity', 0).css('visibility', 'hidden');
    }
}

return {
    showLoading: showLoading,
    hideLoading: hideLoading,
};

});