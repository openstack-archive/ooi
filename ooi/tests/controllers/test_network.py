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

import uuid

import mock

from ooi.api import helpers
from ooi.api import helpers_neutron
from ooi.api import network as network_api
from ooi import exception
from ooi.occi.infrastructure import network as occi_network
from ooi.tests import base
from ooi.tests import fakes_network as fakes


class TestNetworkControllerNeutron(base.TestController):

    def setUp(self):
        super(TestNetworkControllerNeutron, self).setUp()
        self.controller = network_api.Controller(neutron_ooi_endpoint="ff")

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    def test_index(self, m_index):
        test_networks = [
            fakes.networks[fakes.tenants["bar"]["id"]],
            fakes.networks[fakes.tenants["foo"]["id"]]
        ]
        req = fakes.create_req_test(None, None)
        for nets in test_networks:
            ooi_net = helpers_neutron.OpenStackNeutron._build_networks(nets)
            m_index.return_value = ooi_net
            result = self.controller.index(req)
            expected = self.controller._get_network_resources(ooi_net)
            self.assertEqual(result.resources.__len__(),
                             expected.__len__())
            m_index.assert_called_with(req, 'networks', None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "get_network_details")
    def test_show(self, m_network):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for net in test_networks:
            ret = self.controller.show(None, net["id"])
            self.assertIsInstance(ret, occi_network.NetworkResource)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "create_network")
    def test_create(self, m):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for test_net in test_networks:
            parameters = {"occi.core.title": test_net["name"],
                          "org.openstack.network.ip_version": 4,
                          "occi.network.address": "0.0.0.0",
                          }
            categories = {occi_network.NetworkResource.kind,
                          occi_network.ip_network}
            req = fakes.create_req_test_occi(parameters, categories)
            fake_net = fakes.fake_build_net(
                parameters['occi.core.title'],
                parameters['org.openstack.network.ip_version'],
                parameters['occi.network.address']
            )
            m.return_value = fake_net
            ret = self.controller.create(req)
            net = ret.resources.pop()
            self.assertIsInstance(net, occi_network.NetworkResource)
            self.assertEqual(net.title, test_net['name'])

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "create_resource")
    def test_create_error(self, m):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        schema1 = occi_network.NetworkResource.kind.scheme
        net = test_networks[0]
        schemes = {schema1: net}
        parameters = {"occi.core.title": "name",
                      }
        req = fakes.create_req_test(parameters, schemes)

        self.assertRaises(exception.Invalid, self.controller.create, req)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "create_network")
    def test_create_no_ip_mixin(self, m):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for test_net in test_networks:
            parameters = {"occi.core.title": test_net["name"],
                          "org.openstack.network.ip_version": 4,
                          "occi.network.address": "0.0.0.0",
                          }
            categories = {occi_network.NetworkResource.kind}
            req = fakes.create_req_test_occi(parameters, categories)
            fake_net = fakes.fake_build_net(
                parameters['occi.core.title'],
                parameters['org.openstack.network.ip_version'],
                parameters['occi.network.address']
            )
            m.return_value = fake_net
            self.assertRaises(exception.OCCIMissingType,
                              self.controller.create, req)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "delete_network")
    def test_delete(self, m_network):
        m_network.return_value = []
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for net in test_networks:
            ret = self.controller.delete(None, net["id"])
            self.assertEqual(ret, [])
            self.assertEqual(ret.__len__(), 0)

    def test_get_network_resources(self):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        subnet = fakes.subnets
        for net in test_networks:
            net["subnet_info"] = subnet[0]
        ooi_net = (
            helpers_neutron.OpenStackNeutron._build_networks(
                test_networks))
        ret = self.controller._get_network_resources(ooi_net)
        self.assertIsInstance(ret, list)
        self.assertIsNot(ret.__len__(), 0)
        for net_ret in ret:
            self.assertIsInstance(net_ret, occi_network.NetworkResource)

    def test_filter_attributes(self):
        parameters = {"occi.core.title": 'name',
                      "org.openstack.network.ip_version": '4',
                      "occi.network.address": '00001/24',
                      "occi.network.gateway": '00001',
                      }
        categories = {occi_network.NetworkResource.kind}
        req = fakes.create_req_test_occi(parameters, categories)
        occi_scheme = {
            "category": occi_network.NetworkResource.kind,
            "optional_mixins": [
                occi_network.ip_network,
            ]
        }
        ret = network_api.process_parameters(req, occi_scheme)
        self.assertIsNotNone(ret)
        self.assertEqual(parameters, ret)

    def test_filter_attributes_empty(self):
        categories = {occi_network.NetworkResource.kind}
        req = fakes.create_req_test_occi(None, categories)
        occi_scheme = {
            "category": occi_network.NetworkResource.kind,
            "optional_mixins": [
                occi_network.ip_network,
            ]
        }
        attributes = network_api.process_parameters(req, occi_scheme)
        self.assertIsNone(attributes)

    def test_run_action_invalid(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"], path="/network?action=start")
        server_uuid = uuid.uuid4().hex
        self.assertRaises(exception.InvalidAction,
                          self.controller.run_action,
                          req,
                          server_uuid,
                          None)

    def test_run_action_up(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"], path="/network?action=up")
        server_uuid = uuid.uuid4().hex
        self.assertRaises(exception.NotImplemented,
                          self.controller.run_action,
                          req,
                          server_uuid,
                          None)


class TestNetworkControllerNova(base.TestController):

    def setUp(self):
        super(TestNetworkControllerNova, self).setUp()
        self.controller = network_api.Controller(None)

    @mock.patch.object(helpers.OpenStackHelper, "list_networks")
    def test_index(self, m_index):
        test_networks = [
            fakes.networks[fakes.tenants["bar"]["id"]],
            fakes.networks[fakes.tenants["foo"]["id"]]
        ]
        req = fakes.create_req_test(None, None)
        for nets in test_networks:
            ooi_net = helpers.OpenStackHelper._build_networks(nets)
            m_index.return_value = ooi_net
            result = self.controller.index(req)
            expected = self.controller._get_network_resources(ooi_net)
            self.assertEqual(result.resources.__len__(),
                             expected.__len__())
            m_index.assert_called_with(req, None)

    @mock.patch.object(helpers.OpenStackHelper, "get_network_details")
    def test_show(self, m_network):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for net in test_networks:
            ret = self.controller.show(None, net["id"])
            self.assertIsInstance(ret, occi_network.NetworkResource)

    @mock.patch.object(helpers.OpenStackHelper, "create_network")
    def test_create(self, m):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for test_net in test_networks:
            parameters = {"occi.core.title": test_net["name"],
                          "org.openstack.network.ip_version": 4,
                          "occi.network.address": "0.0.0.0",
                          }
            categories = {occi_network.NetworkResource.kind,
                          occi_network.ip_network}
            req = fakes.create_req_test_occi(parameters, categories)
            fake_net = fakes.fake_build_net(
                parameters['occi.core.title'],
                parameters['org.openstack.network.ip_version'],
                parameters['occi.network.address']
            )
            m.return_value = fake_net
            ret = self.controller.create(req)
            net = ret.resources.pop()
            self.assertIsInstance(net, occi_network.NetworkResource)
            self.assertEqual(net.title, test_net['name'])

    @mock.patch.object(helpers.OpenStackHelper, "create_network")
    def test_create_error(self, m):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        schema1 = occi_network.NetworkResource.kind.scheme
        net = test_networks[0]
        schemes = {schema1: net}
        parameters = {"occi.core.title": "name",
                      }
        req = fakes.create_req_test(parameters, schemes)

        self.assertRaises(exception.Invalid, self.controller.create, req)

    @mock.patch.object(helpers.OpenStackHelper, "create_network")
    def test_create_no_ip_mixin(self, m):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for test_net in test_networks:
            parameters = {"occi.core.title": test_net["name"],
                          "org.openstack.network.ip_version": 4,
                          "occi.network.address": "0.0.0.0",
                          }
            categories = {occi_network.NetworkResource.kind}
            req = fakes.create_req_test_occi(parameters, categories)
            fake_net = fakes.fake_build_net(
                parameters['occi.core.title'],
                parameters['org.openstack.network.ip_version'],
                parameters['occi.network.address']
            )
            m.return_value = fake_net
            self.assertRaises(exception.OCCIMissingType,
                              self.controller.create, req)

    @mock.patch.object(helpers.OpenStackHelper, "delete_network")
    def test_delete(self, m_network):
        m_network.return_value = []
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        for net in test_networks:
            ret = self.controller.delete(None, net["id"])
            self.assertEqual(ret, [])
            self.assertEqual(ret.__len__(), 0)

    def test_get_network_resources(self):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        subnet = fakes.subnets
        for net in test_networks:
            net["subnet_info"] = subnet[0]
        ooi_net = (
            helpers_neutron.OpenStackNeutron._build_networks(
                test_networks))
        ret = self.controller._get_network_resources(ooi_net)
        self.assertIsInstance(ret, list)
        self.assertIsNot(ret.__len__(), 0)
        for net_ret in ret:
            self.assertIsInstance(net_ret, occi_network.NetworkResource)

    def test_run_action_invalid(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"], path="/network?action=start")
        server_uuid = uuid.uuid4().hex
        self.assertRaises(exception.InvalidAction,
                          self.controller.run_action,
                          req,
                          server_uuid,
                          None)

    def test_run_action_up(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"], path="/network?action=up")
        server_uuid = uuid.uuid4().hex
        self.assertRaises(exception.NotImplemented,
                          self.controller.run_action,
                          req,
                          server_uuid,
                          None)