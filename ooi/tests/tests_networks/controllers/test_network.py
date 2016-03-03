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
import mock

from ooi.api.networks import helpers
from ooi.api.networks import network
from ooi import exception
from ooi.occi.infrastructure import network_extend
from ooi.tests import base
from ooi.tests.tests_networks import fakes


class TestNetworkController(base.TestController):

    def setUp(self):
        super(TestNetworkController, self).setUp()
        self.controller = network.Controller(None)

    @mock.patch.object(helpers.OpenStackNet, "index")
    def test_index(self, m_index):
        test_networks = [
            fakes.networks[fakes.tenants["bar"]["id"]],
            fakes.networks[fakes.tenants["foo"]["id"]]
        ]
        req = fakes.create_req_test(None, None)
        for nets in test_networks:
            m_index.return_value = nets
            result = self.controller.index(req)
            expected = self.controller._get_network_resources(nets)
            self.assertEqual(result.resources.__len__(),
                             expected.__len__())
            # self.assertEqual(result.resources, expected)
            m_index.assert_called_with(req, None)

    @mock.patch.object(helpers.OpenStackNet, "get_network")
    def test_show(self, m_network):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for net in test_networks:
            ret = self.controller.show(None, net["id"])
            self.assertIsInstance(ret, network_extend.Network)

    @mock.patch.object(helpers.OpenStackNet, "create_network")
    @mock.patch.object(helpers.OpenStackNet, "create_subnet")
    def test_create(self, m_sub, m_network):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        schema1 = network_extend.Network.scheme
        # m_network.return_value = {"id":"xxx"}
        for net in test_networks:
            schemes = {schema1: net}
            parameters = {"occi.core.title": "name",
                          "occi.network.ip_version": 4,
                          "occi.networkinterface.address": "0.0.0.0",
                          }
            req = fakes.create_req_test(parameters, schemes)
            ret = self.controller.create(req)
            self.assertIsInstance(ret, network_extend.Network)

    @mock.patch.object(helpers.OpenStackNet, "create_network")
    @mock.patch.object(helpers.OpenStackNet, "create_subnet")
    def test_create_Error(self, m_sub, m_network):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        schema1 = network_extend.Network.scheme
        net = test_networks[0]
        schemes = {schema1: net}
        parameters = {"occi.core.title": "name",
                      }
        req = fakes.create_req_test(parameters, schemes)

        self.assertRaises(exception.Invalid, self.controller.create, req)

    @mock.patch.object(helpers.OpenStackNet, "delete_network")
    def test_delete(self, m_network):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        # schema1 = network.Network.scheme
        for net in test_networks:
            ret = self.controller.delete(None, net["id"])
            self.assertIsInstance(ret, list)
            self.assertEqual(ret.__len__(), 0)

    def test_get_network_resources(self):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        subnet = fakes.subnets
        for net in test_networks:
            net["subnet_info"] = subnet[0]
        ret = self.controller._get_network_resources(test_networks)
        self.assertIsInstance(ret, list)
        self.assertIsNot(ret.__len__(), 0)
        for net_ret in ret:
            self.assertIsInstance(net_ret, network_extend.Network)

    def test_filter_attributes(self):
        attr_dic = {'attr1': '0', 'attr2': '1', 'attr3': '2'}
        schemes = {"something.schema1": "8923489"}
        req = fakes.create_req_test(attr_dic, schemes)
        ret = self.controller._filter_attributes(req)
        self.assertIsNotNone(ret)
        self.assertEqual(attr_dic, ret)

    def test_filter_attributes_empty(self):
        schemes = {"any": "net"}
        req = fakes.create_req_test(params=None, schemes=schemes)
        attributes = self.controller._filter_attributes(req)
        self.assertIsNone(attributes)
