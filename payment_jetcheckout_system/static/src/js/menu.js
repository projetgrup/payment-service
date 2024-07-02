/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "web.utils";

patch(WebClient.prototype, "payment_jetcheckout_system.menu_main", {
    async loadRouterState() {
        const system = this.user.context.system;
        if (system) {
            const controller = this.actionService.currentController;
            if (controller) {
                const actionId = controller && controller.action.id;
                const menu = this.menuService.getAll().find((m) => m.actionID === actionId && m.xmlid === `payment_${system}.menu_main`);
                const menuID = menu && menu.appID;
                if (menuID) {
                    this.menuService.setCurrentMenu(menuID);
                    return;
                }
            }
        }
        return this._super.apply(this, arguments);
    },
});