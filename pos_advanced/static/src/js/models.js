odoo.define('pos_advanced.models', function (require) {
'use strict';

const PosModel = require('point_of_sale.models');

PosModel.load_fields('res.partner', ['type', 'child_ids']);

});