/** @odoo-module **/


import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { useBus, useEffect, useService } from "@web/core/utils/hooks";
import { useOwnDebugContext } from "@web/core/debug/debug_context";
import { registry } from "@web/core/registry";
import { DebugMenu } from "@web/core/debug/debug_menu";
import { localization } from "@web/core/l10n/localization";
import { useTooltip } from "@web/core/tooltip/tooltip_hook";

const { Component, hooks } = owl;
const { useExternalListener } = hooks;
const rpc = require('web.rpc');

// console.log(registry.category("user_menuitems").remove('odoo_account'));


patch(WebClient.prototype, "whitelabel.WebClient", {
    
    setup() {
        this.menuService = useService("menu");
        this.actionService = useService("action");
        this.title = useService("title");
        this.router = useService("router");
        this.user = useService("user");
        useService("legacy_service_provider");
        useOwnDebugContext({ categories: ["default"] });
        if (this.env.debug) {
            registry.category("systray").add(
                "web.debug_mode_menu",
                {
                    Component: DebugMenu,
                },
                { sequence: 100 }
            );
        }
        this.localization = localization;
        useBus(this.env.bus, "ROUTE_CHANGE", this.loadRouterState);
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", (mode) => {
            if (mode !== "new") {
                this.el.classList.toggle("o_fullscreen", mode === "fullscreen");
            }
        });
        useEffect(
            () => {
                this.loadRouterState();
            },
            () => []
        );
        useExternalListener(window, "click", this.onGlobalClick, { capture: true });
        const self = this;
        rpc.query({
            model: "res.config.settings",
            method: 'get_debranding_settings',
        }, {
            shadow: true
        }).then(function(debranding_settings) {
            odoo.debranding_settings = debranding_settings;
            self.title.setParts({ zopenerp: debranding_settings && debranding_settings.title_brand });
        });
        useTooltip();
    }
});

