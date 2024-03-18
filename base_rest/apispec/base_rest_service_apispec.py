# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import inspect
import textwrap

from odoo import _
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
        company = env.company
        website = getattr(company, 'website_id', False)
        if website:
            url = "/web/image/website/%s/logo" % website.id
        else:
            url = "/web/image/res.company/%s/logo" % company.id

        super(BaseRestServiceAPISpec, self).__init__(
            title=_("%s REST Services") % self._service._usage.capitalize(),
            openapi_version="3.0.0",
            version="",
            info={
                "description": textwrap.dedent(str(getattr(self._service, "_description", "") or "")),
                "x-logo": dict(url=url)
            },
            servers=self._get_servers(),
            plugins=self._get_plugins(),
            tags = [],
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

        company = env.company
        website = getattr(company, 'website_id', False)
        if website:
            url = website.domain
        else:
            url = company.website
        if not url:
            url = env["ir.config_parameter"].sudo().get_param("web.base.url")

        return [
            {
                "url": "%s/%s/%s"
                % (
                    url.strip("/"),
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

    def _get_method_values(self, method):
        summary = textwrap.dedent(str(method.__doc__ or ""))
        values = {'summary': summary}
        tags = method.routing.get('tags')
        if tags:
            values.update({'tags': tags})
        return values

    def _add_path(self, method):
        values = self._get_method_values(method)
        routing = method.routing
        for paths, method in routing["routes"]:
            for path in paths:
                operations = {method.lower(): values}
                self.path(path, operations=operations, routing=routing)

    def _add_webhook(self, method):
        def name(name):
            return ''.join(i and x.capitalize() or x for i, x in enumerate(name.split('_')))

        values = self._get_method_values(method)
        routing = method.routing
        operations = {'post': values}

        for plugin in self.plugins:
            try:
                plugin.operation_helper(operations=operations, routing=routing)
            except:
                continue

        self._clean_operations(operations)

        webhook = {
            name(method.__name__): {
                "post": {
                    **values,
                    "responses": {
                        "200": {
                            "description": _("Return a 200 status to indicate that the data was sent successfully")
                        }
                    }

                }
            }
        }

        if 'webhooks' in self.options:
            self.options['webhooks'].update(webhook)
        else:
            self.options['webhooks'] = webhook

    def generate_methods(self):
        def sort_methods(method):
            try:
                return inspect.getsourcelines(method[1])[1]
            except:
                return -1

        if not self.options:
            self.options = {}

        methods = inspect.getmembers(self._service, inspect.ismethod)
        methods.sort(key=sort_methods)
        for name, method in methods:
            if hasattr(method, "routing"):
                if 'webhook' in method.routing:
                    self._add_webhook(method)
                else:
                    self._add_path(method)
