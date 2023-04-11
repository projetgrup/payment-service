odoo.define('payment_jetcheckout.tools', function (require) {
"use strict";

var core = require('web.core');
var utils = require('web.utils');
var round_di = utils.round_decimals;

function formatCurrency(value, position=false, symbol=false, precision=false) {
    const l10n = core._t.database.parameters;
    const formatted = _.str.sprintf('%.' + precision + 'f', round_di(value, precision) || 0).split('.');
    formatted[0] = utils.insert_thousand_seps(formatted[0]);
    const amount = formatted.join(l10n.decimal_point);
    if (position === 'after') {
        return amount + ' ' + symbol;
    } else {
        return symbol + ' ' + amount;
    }
}

return {
    formatCurrency: formatCurrency,
};
});