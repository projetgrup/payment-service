/** @odoo-module **/

import core from 'web.core';
var AbstractAction = require('web.AbstractAction');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;

var CompanyHierarchy = AbstractAction.extend({
    hasControlPanel: true,
    events: {
        'click .o_company_fold': '_onClickFold',
        'click .o_company_action': '_onClickAction',
    },
    init: function(parent, action) {
        this._super.apply(this, arguments);
        this.actionManager = parent;
        this.given_context = Object.assign({}, session.user_context);
        this.controller_url = action.context.url;
        if (action.context.context) {
            this.given_context = action.context.context;
        }
        this.given_context.active_id = action.context.active_id || action.params.active_id;
        this.given_context.model = action.context.active_model || false;
        this.given_context.ttype = action.context.ttype || false;
        this.given_context.auto_unfold = action.context.auto_unfold || false;
    },
    willStart: function() {
        return Promise.all([this._super.apply(this, arguments), this.get_html()]);
    },
    set_html: function() {
        var self = this;
        var def = Promise.resolve();
        return def.then(function () {
            self.$('.o_content').html(self.html);
            self.renderSearch();
            self.update_cp();
        });
    },
    start: async function() {
        this.controlPanelProps.cp_content = { $buttons: this.$buttons };
        await this._super(...arguments);
        this.set_html();
    },
    get_html: function() {
        var self = this;
        return this._rpc({
                model: 'res.company.hierarchy',
                method: 'get_html',
                args: [this.given_context.searchCompany || false],
                context: this.given_context,
            })
            .then(function (html) {
                self.html = html;
            });
    },
    update_cp: function () {
        var status = {
            cp_content: {
                $buttons: this.$buttonPrint,
                $searchview: this.$searchView
            },
        };
        return this.updateControlPanel(status);
    },
    renderSearch: function () {
        this.$buttonPrint = $(QWeb.render('company.button'));
        this.$buttonPrint.find('button').on('click', this._onCreateCompany.bind(this));
        this.$searchView = $(QWeb.render('company.search'));
        this.$searchView.find('input').on('change', this._onSearchCompany.bind(this));
    },
    _onFold: function (id) {
        var self = this;
        const children = $('.o_company_hierarchy_line[data-parent=' + id + ']');
        children.each(function() {
            self._onFold($(this).data('id'));
        });
        children.toggleClass('d-none d-flex');
    },
    _onClickFold: function (ev) {
        const id = $(ev.currentTarget).parent().data('id');
        $(ev.currentTarget).find('i').toggleClass('fa-caret-right fa-caret-down');
        this._onFold(id);
    },
    _onClickAction: function (ev) {
        ev.preventDefault();
        const company_id = $(ev.currentTarget).parent().parent().data('id');
        const name = $(ev.currentTarget).parent().parent().data('name');
        const model = $(ev.currentTarget).data('model');
        if (!model) {
            alert(_t('This module is working in progress'));
            return;
        }
        const action = {
            type: 'ir.actions.act_window',
            name: name,
            res_model: model,
            views: [[false, 'list'], [false, 'form']],
            target: 'current',
            domain: [['company_id', '=', company_id]]
        }
        if (model === 'res.company') {
            action['res_id'] = company_id;
            action['context'] = {'active_id': company_id};
            action['views'] = [[false, 'form']];
        }
        return this.do_action(action);
    },
    _onCreateCompany: function (ev) {
        ev.preventDefault();
        return this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'res.company',
            views: [[false, 'form']],
            target: 'current'
        });
    },
    _onSearchCompany: function (ev) {
        ev.preventDefault();
        var name = $(ev.currentTarget).val().trim();
        this.given_context.searchCompany = name
        this._reload();
    },
    _reload: function () {
        var self = this;
        return this.get_html().then(function () {
            self.$('.o_content').html(self.html);
        });
    },
});

core.action_registry.add('company_hierarchy', CompanyHierarchy);
export default CompanyHierarchy;