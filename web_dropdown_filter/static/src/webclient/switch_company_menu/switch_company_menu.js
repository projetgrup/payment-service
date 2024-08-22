/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { SwitchCompanyMenu } from "@web/webclient/switch_company_menu/switch_company_menu";
import { symmetricalDifference } from "@web/core/utils/arrays";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useBus } from "@web/core/utils/hooks";
import { patch } from "web.utils";


const { hooks } = owl;
const { useState } = hooks;

patch(SwitchCompanyMenu.prototype, "web_dropdown_filter.SwitchCompanyMenu", {
    setup() {
        this._super.apply(this, arguments);
        this.companyService = useService("company");
        this.state = useState({
            companiesToToggle: [],
            originalCompanies: Object.values(this.companyService.availableCompanies || {}),
        });
        useBus(Dropdown.bus, "state-changed", () => {
            this.companyService.availableCompanies = this.state.originalCompanies;
        });
    },

    toggleCompany(companyId) {
        this.state.companiesToToggle = symmetricalDifference(this.state.companiesToToggle, [
            companyId,
        ]);
    },

    chooseCompany(){
        this.companyService.setCompanies("toggle", ...this.state.companiesToToggle);
    },

    onSearchInput(ev) {
        const companiesObj = this.state.originalCompanies; 
        const searchValue = ev.target.value.trim().toLowerCase();
        if (!searchValue) {
            this.state.filteredCompanies = companiesObj;
        } else {
            const filteredCompanies = companiesObj.filter(company => {
                return company.name.toLowerCase().includes(searchValue);
            });
            this.state.filteredCompanies = filteredCompanies;
        }
        this.companyService.availableCompanies = this.state.filteredCompanies;
    },
});


SwitchCompanyMenu.template = "web_dropdown_filter.SwitchCompanyMenu";
