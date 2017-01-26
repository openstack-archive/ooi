# -*- coding: utf-8 -*-

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
from ooi.occi.infrastructure import ip_reservation
from ooi.occi import validator as occi_validator
from ooi.openstack import network as os_network


class Controller(base.Controller):
    def __init__(self, app=None, openstack_version=None):
        """IP reservation controller initialization

        :param app: application
        :param: openstack_version: nova version
        """

        super(Controller, self).__init__(
            app=app,
            openstack_version=openstack_version)
        self.os_helper = helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    @staticmethod
    def _get_ipreservation_resources(ipreservation_list):
        """Create network instances from ip reservations in json format

        :param ipreservation_list: ip reservation objects provides by
        the cloud infrastructure
        """
        occi_ipreservation_resources = []
        if ipreservation_list:
            for s in ipreservation_list:
                n_id = str(s["id"])  # some versions retrieve int.
                n_name = s["pool"]
                n_address = s["ip"]
                n_used = False
                if s["instance_id"]:
                    n_used = True
                s = ip_reservation.IPReservation(title=n_name,
                                                 id=n_id,
                                                 address=n_address,
                                                 used=n_used
                                                 )
                occi_ipreservation_resources.append(s)
        return occi_ipreservation_resources

    def index(self, req):
        """List ip reservations

        :param req: request object
        """
        occi_ipreservation = self.os_helper.get_floating_ips(req)
        occi_ipreservation_resources = self._get_ipreservation_resources(
            occi_ipreservation)

        return collection.Collection(
            resources=occi_ipreservation_resources)

    def show(self, req, id):
        """Get ip reservation details

        :param req: request object
        :param id: ip reservation identification
        """
        resp = self.os_helper.get_floating_ip(req, id)
        occi_network_resources = self._get_ipreservation_resources(
            [resp])
        return occi_network_resources[0]

    def create(self, req, body=None):
        """Create an ip reservation instance in the cloud

        :param req: request object
        :param body: body request (not used)
        """
        parser = req.get_parser()(req.headers, req.body)
        scheme = {
            "category": ip_reservation.IPReservation.kind,
            "optional_mixins": [
                os_network.OSFloatingIPPool,
            ]
        }
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)
        pool = None
        if os_network.OSFloatingIPPool.scheme in obj["schemes"]:
            pool = (
                obj["schemes"][os_network.OSFloatingIPPool.scheme][0]
            )
        resp = self.os_helper.allocate_floating_ip(req, pool)
        occi_network_resources = self._get_ipreservation_resources(
            [resp])
        return collection.Collection(resources=occi_network_resources)

    def delete(self, req, id):
        """delete an ip reservation instance

        :param req: current request
        :param id: identification
        """
        self.os_helper.release_floating_ip(req, id)
        return []

    def run_action(self, req, id, body):
        """Run action over the network

        :param req: current request
        :param id: ip reservation  identification
        :param body: body
        """
        raise exception.NotImplemented()