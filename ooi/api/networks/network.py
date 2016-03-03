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

import ooi.api.base
from ooi.api.networks import helpers
from ooi.api.networks import parsers
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import network_extend


def _build_network(name, prefix=None):
    if prefix:
        network_id = '/'.join([prefix, name])
    else:
        network_id = name
    return network_extend.Network(title=name, id=network_id, state="active")


class Controller(ooi.api.base.Controller):
    def __init__(self, neutron_endpoint):
        super(Controller, self).__init__(app=None, openstack_version="v2.0")
        self.os_helper = helpers.OpenStackNet(
            neutron_endpoint
        )

    @staticmethod
    def _filter_attributes(req):
        """Get attributes from request parameters

        :param req: request
        """
        try:
            parameters = parsers.process_parameters(req)
            if not parameters:
                return None
            if "attributes" in parameters:
                attributes = {}
                for k, v in parameters.get("attributes", None).items():
                    attributes[k.strip()] = v.strip()
            else:
                attributes = None
        except Exception:
            raise exception.Invalid
        return attributes

    @staticmethod
    def _validate_attributes(required, attributes):
        """Get attributes from request parameters

        :param required: required attributes
        :param attributes: request attributes
        """
        for at in required:
            if at not in attributes:
                raise exception.Invalid()

    @staticmethod
    def _get_network_resources(networks_list):
        """Create network instances from network in json format

        :param networks: networks objects provides by the cloud infrastructure
        """
        # fixme(jorgesece):
        # those attributes should be mapped in driver to occi attr.

        occi_network_resources = []
        if networks_list:
            for s in networks_list:
                s["status"] = parsers.network_status(s["status"])
                n_id = s["id"]
                n_status = s["status"]
                n_name = s["name"]
                if "subnet_info" in s:
                    # fixme(jorgesece) only works with the first subnetwork
                    n_cidr = s["subnet_info"]["cidr"]
                    n_ip_version = s["subnet_info"]["ip_version"]
                    n_gateway = s["subnet_info"]["gateway_ip"]
                    s = network_extend.Network(title=n_name,
                                               id=n_id, state=n_status,
                                               address=n_cidr,
                                               ip_version=n_ip_version,
                                               gateway=n_gateway)
                else:
                    s = network_extend.Network(title=n_name,
                                               id=n_id, state=n_status)
                occi_network_resources.append(s)
        return occi_network_resources

    def index(self, req):
        """List networks filtered by parameters

        :param req: request object
        """
        attributes = self._filter_attributes(req)
        occi_networks = self.os_helper.index(req, attributes)
        occi_network_resources = self._get_network_resources(
            occi_networks)

        return collection.Collection(
            resources=occi_network_resources)

    def show(self, req, id):
        """Get network details

        :param req: request object
        :param id: network identification
        """
        resp = self.os_helper.get_network(req, id)
        occi_network_resources = self._get_network_resources(
            [resp])
        return occi_network_resources[0]

    def create(self, req, body=None):
        """Create a network instance in the cloud

        :param: req: request object
        :param body: body request (not used)
        """
        # todo(jorgesece): manage several creation
        # FIXME(jorgesece): Body is coming from OOI
        # resource class and is not used
        attributes = self._filter_attributes(req)
        self._validate_attributes(
            self.os_helper.required["network"], attributes)
        net = self.os_helper.create_network(req, attributes)
        try:
            attributes["occi.core.id"] = net["id"]
            net["subnet_info"] = self.os_helper.create_subnet(
                req, attributes)
        except Exception as ex:
            self.os_helper.delete_network(req, attributes)
            raise ex
        occi_network_resources = self._get_network_resources([net])
        return occi_network_resources[0]

    def delete(self, req, id):
        """delete networks which satisfy the parameters

        :param req: current request
        :param id: identificator
        """
        # todo(jorgesece): manage several deletion
        attributes = {"occi.core.id": id}
        network = self.os_helper.delete_network(req, attributes)
        if network.status_int == 404:
            raise exception.NotFound()
        return []

    def run_action(self, req, id, body, parameters=None):
        raise exception.NotFound()
