/** @odoo-module alias=paylox.framework **/
"use strict";

function showLoading() {
    const $buttons = $('[field="payment.button"]');
    const $loading = $('.o_loading');
    if ($buttons.length) {
        $buttons.addClass('disabled');
        $buttons.prop('disabled', 'disabled');
    }
    if ($loading.length) {
        $loading.css('opacity', 1).css('visibility', 'visible');
    }
}

function hideLoading() {
    const $buttons = $('[field="payment.button"]');
    const $loading = $('.o_loading');
    if ($buttons.length) {
        $buttons.removeClass('disabled');
        $buttons.prop('disabled', false);
    }
    if ($loading.length) {
        $loading.css('opacity', 0).css('visibility', 'hidden');
    }
}

export default {
    showLoading: showLoading,
    hideLoading: hideLoading,
};
