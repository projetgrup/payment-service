# -*- coding: utf-8 -*-
from odoo import api, models

class ReportCompanyHierarchy(models.AbstractModel):
    _name = 'res.company.hierarchy'
    _description = 'Company Hierarchy'

    @api.model
    def get_html(self, name=False):
        lines = self._get_data(name=name)
        return self.env.ref('payment_jetcheckout_system.company_hierarchy')._render({'lines': lines})

    @api.model
    def _get_children(self, company, companies, child=None):
        cids = [company.id]
        children = []

        items = companies.filtered(lambda x: child and x.id != child.id and x.parent_id.id == company.id or x.parent_id.id == company.id)
        for item in items:
            if not item == child:
                ids, childs = self._get_children(item, companies)
                cids.extend(ids)
                children.append([item, childs])
        return cids, children

    @api.model
    def _get_parents(self, company, companies, company_ids, children=[], name=False):
        pids = [company.id]
        parent = [company, children]

        if not name and company.parent_id and company.parent_id.id in company_ids:
            ids, childs = self._get_children(company.parent_id, companies, company)
            pids.extend(ids)
            childs.append([company, children])

            ids, parent = self._get_parents(company.parent_id, companies, company_ids, childs)
            pids.extend(ids)
        return pids, parent

    @api.model
    def _get_data_line(self, lines, indent=0):
        html = []
        for line in lines:
            html.append(self.env.ref('payment_jetcheckout_system.company_hierarchy_line')._render({'company': line[0], 'indent': indent, 'child': line[1] and True or False}))
            if line[1]:
                html.extend(self._get_data_line(line[1], indent=indent+1))
        return html

    @api.model
    def _get_data(self, name=False):
        lines = []

        company_ids = self.env.context.get('allowed_company_ids') or self.env.companies.ids
        companies = self.env['res.company'].browse(company_ids)
        ids = []
        if name:
            cids = self.env['res.company'].search([('id', 'in', company_ids), ('name', 'not ilike', f'%{name}%')], order='name')
            ids.extend(cids.ids)
        for company in companies:
            if company.id not in ids:
                cids, children = self._get_children(company, companies)
                pids, parent = self._get_parents(company, companies, company_ids, children, name)
                lines.append(parent)
                ids.extend(cids + pids)
        data = self._get_data_line(lines)
        return data
