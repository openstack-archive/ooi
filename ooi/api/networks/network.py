# -*- coding: utf-8 -*-

# Copyright 2015 LIP - Lisbon
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

from ooi import exception
from ooi.api.base import Controller as ControlerBase
from ooi.api.networks.helpers import OpenStackNet  # it was import ooi.api.helpers
from ooi.infrastructure.network_extend import Network
from ooi.occi.core import collection


def _build_network(name, prefix=None):
    if prefix:
        network_id = '/'.join([prefix, name])
    else:
        network_id = name
    return Network(title=name, id=network_id, state="active")


class Controller(ControlerBase):
    def __init__(self, app, neutron_version, neutron_endpoint):
        super(Controller, self).__init__(app=app,openstack_version=neutron_version)
        self.neutron_endpoint = neutron_endpoint
        self.neutron_version = neutron_version
        self.os_helper = OpenStackNet(
            self.app,
            self.neutron_version,
            self.neutron_endpoint
        )

    @staticmethod
    def _filter_attributes(parameters):
        """Get attributes from request parameters
        :param parameters: request parameters
        """
        if parameters:
            attributes = parameters.get("attributes", None)
        else:
            attributes = None
        return attributes

    @staticmethod
    def _get_network_resources(networks):# fixme(jorgesece): those attributes should be mapped in driver to occi attr.
        """Create network instances from network in json format
        :param networks: networks objects provides by the cloud infrastructure
        """
        occi_network_resources = []
        if networks:
            for s in networks:
                if "subnet_info" in s:# fixme(jorgesece) only works with the first subnetwork
                    s = Network(title=s["name"], id=s["id"], address=s["subnet_info"]["cidr"],
                                ip_version=s["subnet_info"]["ip_version"], gateway=s["subnet_info"]["gateway_ip"])
                else:
                    s = Network(title=s["name"], id=s["id"])
                occi_network_resources.append(s)
        return occi_network_resources

    def index(self, req, parameters=None):
        """List networks filtered by parameters
        :param req: request object
        :param parameters: request parameters
        """
        attributes = self._filter_attributes(parameters)
        occi_networks = self.os_helper.index(req, attributes)
        occi_network_resources = self._get_network_resources(occi_networks)

        return collection.Collection(resources=occi_network_resources)

    def show(self, req, id, parameters=None):
        """Get network details
        :param req: request object
        :param id: network identification
        :param parameters: request parameters
        """
        resp = self.os_helper.get_network(req, id)
        occi_network_resources = self._get_network_resources([resp])
        return occi_network_resources[0]

    def create(self, req, parameters, body=None): # todo(jorgesece): manage several creation
        """Create a network instance in the cloud
        :param: req: request object
        :param parameters: request parameters with the new network attributes
        :param body: body request (not used)
        """
        # FIXME(jorgesece): Body is coming from OOI resource class and is not used
        attributes = self._filter_attributes(parameters)
        net = self.os_helper.create_network(req, attributes)
        occi_network_resources = self._get_network_resources([net])

        return occi_network_resources[0]

    def delete(self, req, parameters): # todo(jorgesece): manage several deletion
        """delete networks which satisfy the parameters
        :param parameters:
        """
        attributes = self._filter_attributes(parameters)
        network_id = self.os_helper.delete_network(req, attributes)

        return []

    def run_action(self, req, id, body, parameters = None):
        raise exception.NotFound()
