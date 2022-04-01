# -*- coding: utf-8 -*-
from odoo.addons.base_rest.controllers import main

class StudentAPIController(main.RestController):
    _root_path = "/api/v1/"
    _collection_name = "student.api.services"
    _default_auth = "public"
