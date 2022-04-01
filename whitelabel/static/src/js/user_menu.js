/** @odoo-module **/


import { registry } from "@web/core/registry";
import { DebugMenu } from "@web/core/debug/debug_menu";

const { Component, hooks } = owl;
const { useExternalListener } = hooks;

registry.category("user_menuitems").remove('odoo_account');
registry.category("user_menuitems").remove('documentation');
registry.category("user_menuitems").remove('support');