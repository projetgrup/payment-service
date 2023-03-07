odoo.define('payment_student.StudentList', function (require) {
'use strict';

var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');
var core = require('web.core');

var _t = core._t;

var StudentListController = ListController.extend({
    events: _.extend({}, ListController.prototype.events, {
        'click .o_button_import_student': '_onClickImportStudent',
    }),

    willStart: function() {
        var self = this;
        var ready = this.getSession().user_has_group('payment_student.group_student_manager').then(function (is_admin) {
                if (is_admin) {
                    self.buttons_template = 'StudentListView.buttons';
                }
            });
        return Promise.all([this._super.apply(this, arguments), ready]);
    },

    _onClickImportStudent: function () {
        var action = {
            type: 'ir.actions.act_window',
            res_model: 'payment.student.import',
            name: _t('Import Student'),
            view_mode: 'form',
            views:[[false, 'form']],
            target: 'new',
        };
        this.do_action(action);
    },
});

var StudentListView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: StudentListController,
    }),
});

viewRegistry.add('student_buttons', StudentListView);
});
