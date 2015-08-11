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

from ooi.api import base
from ooi.api import helpers
from ooi.api import network as network_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.occi import validator as occi_validator
from ooi.openstack import network as os_network


class Controller(base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.os_helper = helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def index(self, req):
        floating_ips = self.os_helper.get_floating_ips(req)
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
            floating_ips = self.os_helper.get_floating_ips(req)
            for ip in floating_ips:
                if addr["addr"] == ip["ip"]:
                    net = network.NetworkResource(
                        title="network",
                        id="%s/%s" % (network_api.FLOATING_PREFIX, ip["pool"]))
                    return net, ip["id"]
        raise exception.NetworkNotFound(resource_id=addr)

    def _get_interface_from_id(self, req, id):
        try:
            server_id, server_addr = id.split('_', 1)
        except ValueError:
            raise exception.LinkNotFound(link_id=id)
        s = self.os_helper.get_server(req, server_id)
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
        raise exception.LinkNotFound(link_id=id)

    def show(self, req, id):
        return [self._get_interface_from_id(req, id)]

    def create(self, req, body):
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
            raise exception.NetworkPoolFound(pool=net_id)

        # Allocate IP
        ip = self.os_helper.allocate_floating_ip(req, pool_name)

        # Add it to server
        self.os_helper.associate_floating_ip(req, server_id, ip["id"])
        n = network.NetworkResource(title="network", id=net_id)
        c = compute.ComputeResource(title="Compute", id=server_id)
        l = os_network.OSNetworkInterface(c, n, "mac", ip["ip"])
        return collection.Collection(resources=[l])

    def delete(self, req, id):
        iface = self._get_interface_from_id(req, id)
        if iface.target.id == "fixed":
            raise exception.Invalid()

        # remove floating IP
        server = iface.source.id
        self.os_helper.remove_floating_ip(req, server, iface.address)

        # release IP
        self.os_helper.release_floating_ip(req, iface.ip_id)
        return []
