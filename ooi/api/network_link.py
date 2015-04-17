# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json

import webob.exc

from ooi.api import base
from ooi.api import network as network_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.occi import validator as occi_validator
from ooi.openstack import network as os_network


class Controller(base.Controller):
    def index(self, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req = self._get_req(req, path="/%s/os-floating-ips" % tenant_id)
        response = req.get_response(self.app)
        floating_ips = self.get_from_response(response, "floating_ips", [])
        occi_link_resources = []
        for ip in floating_ips:
            if ip["instance_id"]:
                net_id = "%s/%s" % (network_api.FLOATING_PREFIX, ip["pool"])
                n = network.NetworkResource(title="network", id=net_id)
                c = compute.ComputeResource(title="Compute",
                                            id=ip["instance_id"])
                # TODO(enolfc): get the MAC?
                iface = os_network.OSNetworkInterface(c, n, "mac", ip["ip"])
                occi_link_resources.append(iface)

        return collection.Collection(resources=occi_link_resources)

    def _get_os_network_ip(self, req, addr):
        if addr["OS-EXT-IPS:type"] == "fixed":
            return network.NetworkResource(title="network", id="fixed"), None
        else:
            tenant_id = req.environ["keystone.token_auth"].user.project_id
            req = self._get_req(req, path="/%s/os-floating-ips" % tenant_id)
            response = req.get_response(self.app)
            floating_ips = self.get_from_response(response, "floating_ips", [])
            for ip in floating_ips:
                if addr["addr"] == ip["ip"]:
                    net = network.NetworkResource(
                        title="network",
                        id="%s/%s" % (network_api.FLOATING_PREFIX, ip["pool"]))
                    return net, ip["id"]
        raise webob.exc.HTTPNotFound()

    def _get_interface_from_id(self, req, id):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        try:
            server_id, server_addr = id.split('_', 1)
        except ValueError:
            raise webob.exc.HTTPNotFound()
        path = "/%s/servers/%s" % (tenant_id, server_id)
        req = self._get_req(req, path=path, method="GET")
        response = req.get_response(self.app)
        s = self.get_from_response(response, "server", {})
        addresses = s.get("addresses", {})
        for addr_set in addresses.values():
            for addr in addr_set:
                if addr["addr"] == server_addr:
                    n, ip_id = self._get_os_network_ip(req, addr)
                    c = compute.ComputeResource(title="Compute",
                                                id=server_id)
                    # TODO(enolfc): get the MAC?
                    return os_network.OSNetworkInterface(c, n, "mac",
                                                         addr["addr"], ip_id)
        raise webob.exc.HTTPNotFound()

    def show(self, req, id):
        return [self._get_interface_from_id(req, id)]

    def create(self, req, body):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        parser = req.get_parser()(req.headers, req.body)
        scheme = {"category": network_link.NetworkInterface.kind}
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        attrs = obj.get("attributes", {})
        server_id = attrs.get("occi.core.source")
        net_id = attrs.get("occi.core.target")

        # net_id is something like "fixed" or "floating/<pool_name>"
        if net_id == "fixed":
            raise exception.Invalid()
        try:
            _, pool_name = net_id.split("/", 1)
        except ValueError:
            raise webob.exc.HTTPNotFound()

        # Allocate IP
        path = "/%s/os-floating-ips" % tenant_id
        req = self._get_req(req, path="/%s/os-floating-ips" % tenant_id,
                            body=json.dumps({"pool": pool_name}),
                            method="POST")
        response = req.get_response(self.app)
        ip = self.get_from_response(response, "floating_ip", {})

        # Add it to server
        req_body = {"addFloatingIp": {"address": ip["ip"]}}
        path = "/%s/servers/%s/action" % (tenant_id, server_id)
        req = self._get_req(req, path=path, body=json.dumps(req_body),
                            method="POST")
        response = req.get_response(self.app)
        if response.status_int != 202:
            raise base.exception_from_response(response)
        n = network.NetworkResource(title="network", id=net_id)
        c = compute.ComputeResource(title="Compute", id=server_id)
        l = os_network.OSNetworkInterface(c, n, "mac", ip["ip"])
        return collection.Collection(resources=[l])

    def delete(self, req, id):
        iface = self._get_interface_from_id(req, id)
        if iface.target.id == "fixed":
            raise exception.Invalid()

        # remove floating IP
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req_body = {"removeFloatingIp": {"address": iface.address}}
        path = "/%s/servers/%s/action" % (tenant_id, iface.source.id)
        req = self._get_req(req, path=path, body=json.dumps(req_body),
                            method="POST")
        response = req.get_response(self.app)
        if response.status_int != 202:
            raise base.exception_from_response(response)

        # release IP
        path = "/%s/os-floating-ips/%s" % (tenant_id, iface.ip_id)
        req = self._get_req(req, path=path, body=json.dumps(req_body),
                            method="DELETE")
        response = req.get_response(self.app)
        if response.status_int != 202:
            raise base.exception_from_response(response)
        return []
