/** @odoo-module **/

import { RPCErrorDialog, odooExceptionTitleMap } from "@web/core/errors/error_dialogs";
import { patch } from "@web/core/utils/patch";


patch(RPCErrorDialog.prototype, "whitelabel.Dialog", {

    inferTitle() {
        // If the server provides an exception name that we have in a registry.
        if (this.props.exceptionName && odooExceptionTitleMap.has(this.props.exceptionName)) {
            this.title = odooExceptionTitleMap.get(this.props.exceptionName).toString();
            return;
        }
        // Fall back to a name based on the error type.
        if (!this.props.type) return;
        switch (this.props.type) {

            case "server":
                this.title = this.env._t("Odoo Server Error");
                break;
            case "script":
                this.title = this.env._t("Odoo Client Error");
                break;
            case "network":
                this.title = this.env._t("Odoo Network Error");
                break;
        }
        this.title = this.title.replace('Odoo', odoo.debranding_settings.odoo_text_replacement)
    }
});