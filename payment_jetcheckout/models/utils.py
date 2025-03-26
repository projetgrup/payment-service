# -*- coding: utf-8 -*-

def get_main_company(company):
    if company.parent_id:
        return get_main_company(company.parent_id)
    return company
