/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "web.utils";

patch(WebClient.prototype, "payment_jetcheckout_system.menu_main", {
    async loadRouterState() {
        const _super = this._super;
        const system = this.user.context.system;
        if (system) {
            let state = await this.actionService.loadState();
            let menuID = Number(this.router.current.hash.menu_id || 0);
            if (state && !menuID) {
                const controller = this.actionService.currentController;
                const actionId = controller && controller.action.id;
                const menu = this.menuService.getAll().find((m) => m.actionID === actionId && m.xmlid === `payment_${system}.menu_main`);
                menuID = menu && menu.appID;
                if (menuID) {
                    this.menuService.setCurrentMenu(menuID);
                    return;
                }
            }
        }
        return _super.apply(this, arguments);
    },
});