# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
# Copyright 2015 LIP - INDIGO-DataCloud
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
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.occi import validator as occi_validator
from ooi.openstack import helpers as os_helpers
from ooi.openstack import network as os_network


def _get_network_link_resources(link_list):
    """Create OCCI networkLink instances from json format

    :param link_list: provides by the cloud infrastructure
    """
    occi_network_resources = []
    if link_list:
        for l in link_list:
            compute_id = l['compute_id']
            mac = l.get('mac', None)
            net_pool = l.get('pool', None)
            ip = l.get('ip', None)
            state = l.get('state', None)
            ip_id = l.get('ip_id', None)
            net_id = l['network_id']
            n = network.NetworkResource(title="network",
                                        id=net_id)
            c = compute.ComputeResource(title="Compute",
                                        id=compute_id
                                        )
            iface = os_network.OSNetworkInterface(c, n, mac, ip,
                                                  pool=net_pool,
                                                  ip_id=ip_id,
                                                  state=state)
            occi_network_resources.append(iface)
    return occi_network_resources


class Controller(base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.os_helper = helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def index(self, req):
        """List NetworkLinks

        :param req: request object
        """
        link_list = self.os_helper.list_compute_net_links(req)
        occi_link_resources = _get_network_link_resources(link_list)
        return collection.Collection(resources=occi_link_resources)

    def _get_interface_from_id(self, req, id):
        """Get interface from id

        :param req: request object
        :param id: network link identification
        """
        try:
            server_id, network_id, server_addr = id.split('_', 2)
        except ValueError:
            raise exception.LinkNotFound(link_id=id)
        try:
            link = self.os_helper.get_compute_net_link(
                req,
                server_id,
                network_id,
                server_addr)
            occi_instance = _get_network_link_resources([link])[0]
        except Exception:
            raise exception.LinkNotFound(link_id=id)
        return occi_instance

    def show(self, req, id):
        """Get networkLink details

        :param req: request object
        :param id: networkLink identification
        """
        occi_instance = self._get_interface_from_id(req, id)

        return occi_instance

    def create(self, req, body=None):
        """Create a networkLink

        Creates a link between a server and a network.
        It could be fixed or floating IP.

        :param req: request object
        :param body: body request (not used)
        """
        parser = req.get_parser()(req.headers, req.body)
        scheme = {
            "category": network_link.NetworkInterface.kind,
            "optional_mixins": [
                os_network.OSFloatingIPPool,
            ]
        }
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        attrs = obj.get("attributes", {})
        _, net_id = helpers.get_id_with_kind(
            req,
            attrs.get("occi.core.target"),
            network.NetworkResource.kind)
        _, server_id = helpers.get_id_with_kind(
            req,
            attrs.get("occi.core.source"),
            compute.ComputeResource.kind)
        pool = None
        if os_network.OSFloatingIPPool.scheme in obj["schemes"]:
                pool = (
                    obj["schemes"][os_network.OSFloatingIPPool.scheme][0]
                )
        # Allocate public IP and associate it ot the server
        if net_id == os_helpers.PUBLIC_NETWORK:
            os_link = self.os_helper.assign_floating_ip(
                req, net_id, server_id, pool
            )
        else:
            # Allocate private network
            os_link = self.os_helper.create_port(
                req, net_id, server_id)
        occi_link = _get_network_link_resources([os_link])
        return collection.Collection(resources=occi_link)

    def delete(self, req, id):
        """Delete networks link

        :param req: current request
        :param id: identification
        """
        iface = self._get_interface_from_id(req, id)
        server = iface.source.id
        if iface.target.id == os_helpers.PUBLIC_NETWORK:
            # remove floating IP
            self.os_helper.remove_floating_ip(req, server,
                                              iface.address)

            # release IP
            self.os_helper.release_floating_ip(req,
                                               iface.ip_id)
        else:
            self.os_helper.delete_port(
                req, server, iface.ip_id)
        return []