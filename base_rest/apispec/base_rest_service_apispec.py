# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import inspect
import textwrap
import ast

from apispec import APISpec

from ..core import _rest_services_databases
from .rest_method_param_plugin import RestMethodParamPlugin
from .rest_method_security_plugin import RestMethodSecurityPlugin
from .restapi_method_route_plugin import RestApiMethodRoutePlugin


class BaseRestServiceAPISpec(APISpec):
    """
    APISpec object from base.rest.service component
    """

    def __init__(self, service_component, **params):
        self._service = service_component
        env = self._service.env
        super(BaseRestServiceAPISpec, self).__init__(
            title="%s REST Services" % self._service._usage.capitalize(),
            version="",
            openapi_version="3.0.0",
            info={
                "description": textwrap.dedent(
                    getattr(self._service, "_description", "") or ""
                )
            },
            servers=self._get_servers(),
            plugins=self._get_plugins(),
            tags = [{
                "name": "API Description",
                "description": textwrap.dedent(getattr(self._service, "_description", "") or ""),
                #"externalDocs": {
                #    "description": "You can take a look at postman collection",
                #    "url": "/api/v1/%s/postman" % self._service._usage
                #}
            }]
        )
        self._params = params

    def _get_servers(self):
        env = self._service.env
        services_registry = _rest_services_databases.get(env.cr.dbname, {})
        collection_path = ""
        for path, spec in list(services_registry.items()):
            if spec["collection_name"] == self._service._collection:
                collection_path = path
                break
        base_url = env["ir.config_parameter"].sudo().get_param("web.base.url")
        return [
            {
                "url": "%s/%s/%s"
                % (
                    base_url.strip("/"),
                    collection_path.strip("/"),
                    self._service._usage,
                )
            }
        ]

    def _get_plugins(self):
        return [
            RestApiMethodRoutePlugin(self._service),
            RestMethodParamPlugin(self._service),
            RestMethodSecurityPlugin(self._service),
        ]

    def _add_method_path(self, method):
        doc = textwrap.dedent(method.__doc__ or "")
        values = {'summary': doc, 'tags': 'Other'}
        if doc:
            vals = doc.split("\n")
            for val in vals:
                if not val:
                    continue
                if ':' in val:
                    key, value = val.split(':')
                    values[key] = ast.literal_eval(value.strip())
                else:
                    values['summary'] = val

        routing = method.routing
        for paths, method in routing["routes"]:
            for path in paths:
                operations = {method.lower(): values}
                self.path(path, operations=operations, routing=routing)

    def generate_paths(self):
        def sort_methods(method):
            try:
                return inspect.getsourcelines(method[1])[1]
            except:
                return -1

        methods = inspect.getmembers(self._service, inspect.ismethod)
        methods.sort(key=sort_methods)
        for name, method in methods:
            routing = getattr(method, "routing", None)
            if not routing:
                continue
            self._add_method_path(method)
