/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { patch } from "web.utils";

patch(WebClient.prototype, "payment_jetcheckout_system.DefaultAppsMenu", {
    _loadDefaultApp() {
        const system = this.user.context.system;
        if (system) {
            const menu = this.menuService.getAll().find(m => m.xmlid === `payment_${system}.menu_main`);
            if (menu) {
                return this.menuService.selectMenu(menu.id);
            }
        }
        return super._loadDefaultApp();
    },
});