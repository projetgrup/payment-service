odoo.define('connector_syncops.SyncController', function (require) {
'use strict';

const { registry } = require("@web/core/registry");

const ControlPanel = require('web.ControlPanel');
const ListController = require('web.ListController');
const ListView = require('web.ListView');
const viewRegistry = require('web.view_registry');
const core = require('web.core');

const _t = core._t;
const qweb = core.qweb;


const actionHandlersRegistry = registry.category('action_handlers');
actionHandlersRegistry.add('syncops.sync.wizard.reload', ({ options }) => {
    options.onClose();
});


class SyncControlPanel extends ControlPanel {}
SyncControlPanel.template = 'connector_syncops.ControlPanel';


const SyncController = ListController.extend({
    events: _.extend({}, ListController.prototype.events, {
        'click .o_button_import_transaction': '_onClickImportTransaction',
    }),

    renderButtons: function ($node) {
        if ($node && $node[0] && $node[0]['nodeName'] === 'FOOTER') {
            const $buttons = $(qweb.render('connector_syncops.sync_buttons', {widget: this}));
            $buttons.on('click', '.o_list_button_sync', this._onSync.bind(this));
            $buttons.on('click', '.o_list_button_discard', this._onClose.bind(this));
            $buttons.appendTo($node);
            return;
        }
        return this._super.apply(this, arguments);
    },

    _onSync: async function (ev) {
        const node = $(ev.currentTarget);
        this._disableButtons();
        const state = this.model.get(this.handle);
 
        try {
            const actionData = Object.assign({}, {
                type: 'object',
                resModel: 'syncops.sync.wizard',
                name: 'sync',
                resId: null,
                resIds: null,
            });

            const recordData = {
                context: state.getContext(),
                model: 'syncops.sync.wizard',
            };
            await this._executeButtonAction(actionData, recordData);
        } finally {
            this._enableButtons();
        }
    },

    _onClose: function () {
        this.do_action({'type': 'ir.actions.act_window_close'})
    },
});


const SyncView = ListView.extend({
    config: _.extend({}, ListView.prototype.config, {
        Controller: SyncController,
        ControlPanel: SyncControlPanel,
    }),
    searchMenuTypes: ['filter'],
    withBreadcrumbs: false,
});

viewRegistry.add('syncops_sync', SyncView);
});
