/** @odoo-module **/

import rpc from 'web.rpc';
import { actionService } from "@web/webclient/actions/action_service";

const actionStart = actionService.start;
actionService.start = async function start(env) {
    const res = actionStart(env);

    window.addEventListener('beforeunload', (event) => {
        const model = res.currentController?.action?.res_model;
        if (model) {
            const name = res.currentController?.action?.name;
            const view = res.currentController?.view?.type;
            const record = res.currentController?.action?.props?.state?.currentId;
    
            rpc.query({
                route: '/reconciliation/log',
                params: {
                    action: 'close',
                    view: name ? `${name} (${view})` : view,
                    record: `${model},${record || 0}`,
                },
            });
        }
    });

    const log = async function ({ view, record }) {
        if (view) {
            rpc.query({
                route: '/security/audit/log',
                params: { action:'view', view, record },
            });
        }
    }

    const _doAction = res.doAction;
    res.doAction = async function () {
        const r = _doAction.apply(this, arguments);
        return r.then(() => {
            const model = res.currentController?.action?.res_model;
            if (model) {
                const name = res.currentController?.action?.name;
                const view = res.currentController?.view?.type;
                const record = res.currentController?.action?.props?.state?.currentId;
                log({
                    view: name ? `${name} (${view})` : view,
                    record: `${model},${record || 0}`,
                });
            }
        });
    };

    const _switchView = res.switchView;
    res.switchView = async function (viewType, props) {
        const r = _switchView.apply(this, arguments);
        const name = res.currentController?.action?.name;
        const model = res.currentController?.action?.res_model;
        if (model) {
            log({
                view: name ? `${name} (${viewType})` : viewType,
                record: `${model},${props.resId || 0}`,
            });
        }
        return r;
    };

    const _restore = res.restore;
    res.restore = async function () {
        const r = _restore.apply(this, arguments);
        return r.then(() => {
            const model = res.currentController?.action?.res_model;
            if (model) {
                const name = res.currentController?.action?.name;
                const view = res.currentController?.view?.type;
                const record = res.currentController?.action?.props?.state?.currentId;
                log({
                    view: name ? `${name} (${view})` : view,
                    record: `${model},${record || 0}`,
                });
            }
        });
    };

    return res;
}
