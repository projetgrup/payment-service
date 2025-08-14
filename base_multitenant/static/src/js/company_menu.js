/** @odoo-module **/

import { useService } from '@web/core/utils/hooks';
import { SwitchCompanyMenu } from '@web/webclient/switch_company_menu/switch_company_menu';
import { symmetricalDifference } from '@web/core/utils/arrays';
import { patch } from 'web.utils';

const { hooks } = owl;
const { useState } = hooks;

patch(SwitchCompanyMenu.prototype, 'base_multitenant.SwitchCompanyMenu', {
    setup() {
        this._super.apply(this, arguments);
        this.companyService = useService('company');
        this.availableCompanies = Object.values(this.companyService.availableCompanies || {});
        this.state = useState({
            companiesToToggle: [],
            companies: this.availableCompanies,
        });
    },

    toggleCompany(companyId) {
        this.state.companiesToToggle = symmetricalDifference(this.state.companiesToToggle, [companyId]);
    },

    chooseCompany(){
        this.companyService.setCompanies('toggle', ...this.state.companiesToToggle);
    },

    onSearchInput(ev) {
        let filteredCompanies;
        const searchValue = ev.target.value.trim().toLowerCase();
        if (!searchValue) {
            filteredCompanies = this.availableCompanies;
        } else {
            filteredCompanies = this.availableCompanies.filter(company => {
                return company.name.toLowerCase().includes(searchValue);
            });
            for (const company of [...filteredCompanies]) {
                if (company.parent_id && !filteredCompanies.find(c => c.id == company.parent_id)) {
                    filteredCompanies.push(this.companyService.availableCompanies[company.parent_id]);
                }
            }
        }
        this.state.companies = filteredCompanies;
    },
});

SwitchCompanyMenu.template = 'base_multitenant.SwitchCompanyMenu';
