/** @odoo-module alias=paylox.tools **/

import core from 'web.core';
import utils from 'web.utils';

const round_di = utils.round_decimals;

function formatFloat(value, precision=2) {
    const l10n = core._t.database.parameters;
    const formatted = _.str.sprintf('%.' + precision + 'f', round_di(value, precision) || 0).split('.');
    formatted[0] = utils.insert_thousand_seps(formatted[0]);
    return formatted.join(l10n.decimal_point);
}

function formatPercentage(value, position=false, precision=2) {
    const number = formatFloat(value, precision);
    if (position === 'after') {
        return number + '%';
    } else {
        return '%' + number;
    }
}

function formatCurrency(value, position=false, symbol='', precision=2) {
    const amount = formatFloat(value, precision);
    if (position === 'after') {
        return amount + ' ' + symbol;
    } else {
        return symbol + ' ' + amount;
    }
}

function formatDate(value, format='DD-MM-YYYY') {
    return value && moment(value).format(format) || ''
}

export default {
    format: {
        float: formatFloat,
        percentage: formatPercentage,
        currency: formatCurrency,
        date: formatDate,
    }
};