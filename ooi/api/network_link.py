# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
# Copyright 2016 LIP - Lisbon
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
from ooi.openstack import network as os_network


def _get_network_link_resources(link_list):
    """Create OCCI networkLink instances from json format

    :param link_list: provides by the cloud infrastructure
    """
    occi_network_resources = []
    if link_list:
        for l in link_list:
            compute_id = l['compute_id']
            mac = l["mac"]
            net_pool = l['pool']
            ip = l['ip']
            state = l['state']
            if net_pool:  # mac is public network id
                net_id = network_api.PUBLIC_NETWORK
            else:
                net_id = l['network_id']
            n = network.NetworkResource(title="network",
                                        id=net_id)
            c = compute.ComputeResource(title="Compute",
                                        id=compute_id
                                        )
            iface = os_network.OSNetworkInterface(c, n, mac, ip,
                                                  pool=net_pool,
                                                  state=state)
            occi_network_resources.append(iface)
    return occi_network_resources


class Controller(base.Controller):
    def __init__(self, neutron_endpoint):
        self.os_neutron_helper = helpers.OpenStackNeutron(
            neutron_endpoint
        )

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
            link = self.os_neutron_helper.get_compute_net_link(
                req,
                server_id,
                network_id,
                server_addr)
            occi_instance = _get_network_link_resources([link])[0]
        except Exception:
            raise exception.LinkNotFound(link_id=id)
        return occi_instance

    def index(self, req):
        """List networksLinks

        :param req: request object
        """
        attributes = network_api.process_parameters(req)
        link_list = self.os_neutron_helper.list_compute_net_links(
            req,
            attributes)
        occi_link_resources = _get_network_link_resources(link_list)
        return collection.Collection(resources=occi_link_resources)

    def show(self, req, id):
        """Get networkLink details

        :param req: request object
        :param id: networkLink identification
        """
        return self._get_interface_from_id(req, id)

    def create(self, req, body=None):
        """Create a networkLink

        Creates a link between a server and a network.
        It could be fixed or floating IP.

        :param req: request object
        :param body: body request (not used)
        """
        scheme = {
            "category": network_link.NetworkInterface.kind,
            "optional_mixins": [
                os_network.OSFloatingIPPool,
            ]
        }
        parameters = network_api.process_parameters(req, scheme)
        net_id = parameters['occi.core.target']

        # todo(jorgesece): only support one public network,
        # so, supports only one pool. Discuss about pools

        # Allocate public IP and associate it ot the server
        if net_id == network_api.PUBLIC_NETWORK:
            os_link = self.os_neutron_helper.assign_floating_ip(
                req,
                parameters)
        else:
            # Allocate private network
            os_link = self.os_neutron_helper.create_port(
                req, parameters)
        occi_link = _get_network_link_resources([os_link])
        return collection.Collection(resources=occi_link)

    def delete(self, req, id):
        """Delete networks link

        :param req: current request
        :param id: identification
        """
        iface = self._get_interface_from_id(req, id)
        if iface.target.id == network_api.PUBLIC_NETWORK:
            os_link = self.os_neutron_helper.release_floating_ip(
                req, iface.address)
        else:
            os_link = self.os_neutron_helper.delete_port(
                req, iface.mac)
        return os_link
