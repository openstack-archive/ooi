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

import mock

from ooi.api import helpers
from ooi.api import ip_reservation as ip_reservation_control
from ooi.occi.infrastructure import ip_reservation
from ooi.openstack import network as os_network
from ooi.tests import base
from ooi.tests import fakes
from ooi.tests import fakes_network as fake_nets


class TestIPReservationController(base.TestController):
    def setUp(self):
        super(TestIPReservationController, self).setUp()
        self.controller = ip_reservation_control.Controller(
            mock.MagicMock(), None
        )

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ips")
    def test_index_empty(self, m_iplist):
        tenant = fakes.tenants["foo"]
        floating_list = fakes.floating_ips[tenant["id"]]
        m_iplist.return_value = floating_list
        result = self.controller.index(None)
        expected = self.controller._get_ipreservation_resources(floating_list)
        self.assertEqual(expected, result.resources)
        self.assertEqual([], result.resources)
        m_iplist.assert_called_with(None)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ips")
    def test_index(self, m_iplist):
        tenant = fakes.tenants["baz"]
        floating_list = fakes.floating_ips[tenant["id"]]
        m_iplist.return_value = floating_list
        result = self.controller.index(None)
        expected = self.controller._get_ipreservation_resources(floating_list)
        self.assertEqual(expected, result.resources)
        m_iplist.assert_called_with(None)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip")
    def test_show(self, m_ip):
        tenant = fakes.tenants["baz"]
        floating_ip = fakes.floating_ips[tenant["id"]][0]
        m_ip.return_value = floating_ip
        result = self.controller.show(None, floating_ip["id"])
        expected = self.controller._get_ipreservation_resources(
            [floating_ip])[0]
        self.assertIsInstance(result, ip_reservation.IPReservation)
        self.assertEqual(expected, result)
        m_ip.assert_called_with(None, floating_ip["id"])

    @mock.patch.object(helpers.OpenStackHelper,
                       "release_floating_ip")
    def test_delete(self, mock_release):
        tenant = fakes.tenants["baz"]
        floating_ip = fakes.floating_ips[tenant["id"]][0]
        mock_release.return_value = []
        self.controller.delete(None, floating_ip["id"])
        mock_release.assert_called_with(None, floating_ip["id"])

    @mock.patch.object(helpers.OpenStackHelper,
                       "allocate_floating_ip")
    def test_create(self, mock_allocate):
        tenant = fakes.tenants["baz"]
        floating_list = fakes.floating_ips[tenant["id"]][0]
        mock_allocate.return_value = floating_list
        parameters = {}
        categories = {ip_reservation.IPReservation.kind}
        req = fake_nets.create_req_test_occi(parameters, categories)

        result = self.controller.create(req)

        expected = self.controller._get_ipreservation_resources(
            [floating_list])
        self.assertEqual(expected, result.resources)
        mock_allocate.assert_called_with(req, None)

    @mock.patch.object(helpers.OpenStackHelper, "allocate_floating_ip")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_pool(self, mock_validator, mock_allocate):
        tenant = fakes.tenants["baz"]
        floating_list = fakes.floating_ips[tenant["id"]][0]
        mock_allocate.return_value = floating_list
        pool_name = "public"
        obj = {
            "attributes": {},
            "schemes": {
                os_network.OSFloatingIPPool.scheme: [pool_name],
            }
        }
        parameters = {}
        categories = {ip_reservation.IPReservation.kind}
        req = fake_nets.create_req_test_occi(parameters, categories)

        req.get_parser = mock.MagicMock()
        req.get_parser.return_value.return_value.parse.return_value = obj
        mock_validator.validate.return_value = True

        result = self.controller.create(req)

        expected = self.controller._get_ipreservation_resources(
            [floating_list])
        self.assertEqual(expected, result.resources)
        mock_allocate.assert_called_with(req, pool_name)