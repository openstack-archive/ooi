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
from ooi.api import helpers_neutron
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import network
from ooi.occi import validator as occi_validator
from ooi.openstack import network as os_network


def parse_validate_schema(req, scheme=None,
                          required_attr=None):
    """Parse attributes and validate scheme


    Returns attributes from request
    If scheme is specified, it validates the OCCI scheme:
     -Raises exception in case of being invalid

    :param req: request
    :param: scheme: scheme to validate
    :param: required_attr: attributes required
    """
    parser = req.get_parser()(req.headers, req.body)
    if scheme:
        attributes = parser.parse()
        validator = occi_validator.Validator(attributes)
        validator.validate(scheme)
        validator.validate_attributes(required_attr)
    else:
        attributes = parser.parse_attributes(req.headers)
    return attributes


def process_parameters(req, scheme=None,
                       required_attr=None):
    """Get attributes from request parameters

    :param req: request
    :param: scheme: scheme to validate
    :param: required_attr: attributes required
    """
    parameters = parse_validate_schema(req, scheme, required_attr)
    try:
        attributes = {}
        if 'X_PROJECT_ID' in req.headers:
            attributes["X_PROJECT_ID"] = req.headers["X_PROJECT_ID"]
        if "attributes" in parameters:
            for k, v in parameters.get("attributes", None).items():
                attributes[k.strip()] = v.strip()
        if not attributes:
            attributes = None
    except Exception:
        raise exception.Invalid
    return attributes


class Controller(base.Controller):
    def __init__(self, app=None, openstack_version=None,
                 neutron_ooi_endpoint=None):
        """Network controller initialization

        :param app: application
        :param: openstack_version: nova version
        :param: neutron_ooi_endpoint: This parameter
        indicates the Neutron endpoint to load the Neutron Helper.
        If it is None, nova-network is used.
        """

        super(Controller, self).__init__(
            app=app,
            openstack_version=openstack_version)
        if neutron_ooi_endpoint:
            self.os_helper = helpers_neutron.OpenStackNeutron(
                neutron_ooi_endpoint
            )
        else:
            self.os_helper = helpers.OpenStackHelper(
                self.app,
                self.openstack_version
            )

    @staticmethod
    def _get_network_resources(networks_list):
        """Create network instances from network in json format

        :param networks_list: networks objects provides by
        the cloud infrastructure
        """
        occi_network_resources = []
        if networks_list:
            for s in networks_list:
                n_state = s['state']
                n_id = s["id"]
                n_name = s["name"]
                n_address = s.get("address", None)
                n_ip_version = s.get("ip_version", None)
                n_gateway = s.get("gateway", None)
                s = os_network.OSNetworkResource(title=n_name,
                                                 id=n_id, state=n_state,
                                                 ip_version=n_ip_version,
                                                 address=n_address,
                                                 gateway=n_gateway)
                occi_network_resources.append(s)
        return occi_network_resources

    def index(self, req):
        """List networks

        :param req: request object
        """
        occi_networks = self.os_helper.list_networks(req)
        occi_network_resources = self._get_network_resources(
            occi_networks)

        return collection.Collection(
            resources=occi_network_resources)

    def show(self, req, id):
        """Get network details

        :param req: request object
        :param id: network identification
        """
        resp = self.os_helper.get_network_details(req, id)
        occi_network_resources = self._get_network_resources(
            [resp])
        return occi_network_resources[0]

    def create(self, req, body=None):
        """Create a network instance in the cloud

        :param req: request object
        :param body: body request (not used)
        """
        scheme = {
            "category": network.NetworkResource.kind,
            "mixins": [
                network.ip_network,
            ],
            "optional_mixins": [
                os_network.OSNetwork()
            ]
        }
        required = ["occi.core.title",
                    "occi.network.address",
                    ]
        attributes = process_parameters(req, scheme, required)
        name = attributes.get('occi.core.title')
        cidr = attributes.get('occi.network.address')
        gateway = attributes.get('occi.network.gateway', None)
        ip_version = attributes.get('org.openstack.network.ip_version', None)
        net = self.os_helper.create_network(req, name=name,
                                            cidr=cidr,
                                            gateway=gateway,
                                            ip_version=ip_version)
        occi_network_resources = self._get_network_resources([net])
        return collection.Collection(
            resources=occi_network_resources)

    def delete(self, req, id):
        """delete networks which satisfy the parameters

        :param req: current request
        :param id: identification
        """
        response = self.os_helper.delete_network(req, id)
        return response

    def run_action(self, req, id, body):
        """Run action over the network

        :param req: current request
        :param id: network identification
        :param body: body
        """
        action = req.GET.get("action", None)
        occi_actions = [a.term for a in network.NetworkResource.actions]

        if action is None or action not in occi_actions:
            raise exception.InvalidAction(action=action)
        raise exception.NotImplemented("Network actions are not implemented")