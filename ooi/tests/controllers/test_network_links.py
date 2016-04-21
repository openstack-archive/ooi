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

import collections
import uuid

import mock

from ooi.api import helpers
from ooi.api import network as network_api
from ooi.api import network_link as network_link_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.openstack import network as os_network
from ooi.tests import base
from ooi.tests import fakes_neutron as fake_nets


class TestNetworkLinkController(base.TestController):
    def setUp(self):
        super(TestNetworkLinkController, self).setUp()
        self.controller = network_link_api.Controller(None)

    @mock.patch.object(helpers.OpenStackNeutron, "list_compute_net_links")
    def test_index(self, mock_list):
        req = fake_nets.create_req_test(None, None)
        tenant = fake_nets.tenants['foo']
        os_link_list = fake_nets.network_links[tenant["id"]]
        links = []
        for os_link in os_link_list:
            l = fake_nets.fake_build_link(
                os_link['network_id'], os_link['instance_id'], os_link['ip'],
                mac=None, pool=os_link['pool'], state=os_link['status']
            )
            links.append(l)
        mock_list.return_value = links
        ret = self.controller.index(req)
        self.assertIsInstance(ret, collection.Collection)
        if tenant["name"] == "foo":
            for idx, ip in enumerate(os_link_list):
                if ip["instance_id"]:
                    self.assertIsInstance(ret.resources[idx],
                                          os_network.OSNetworkInterface)
        else:
            self.assertEqual([], ret.resources)
        mock_list.assert_called_with(req, None)

    @mock.patch.object(helpers.OpenStackNeutron, "list_compute_net_links")
    def test_index_Empty(self, mock_list):
        req = fake_nets.create_req_test(None, None)
        links = []
        mock_list.return_value = links
        ret = self.controller.index(req)
        self.assertIsInstance(ret, collection.Collection)
        self.assertEqual(ret.resources.__len__(), 0)

    @mock.patch.object(helpers.OpenStackNeutron, "delete_port")
    @mock.patch.object(network_link_api.Controller, "_get_interface_from_id")
    def test_delete_fixed(self, mock_get, mock_remove):
        class FakeNetworkLink(object):
            target = collections.namedtuple("Target", ["id"])("234234")
            source = collections.namedtuple("Source", ["id"])(uuid.uuid4().hex)
            address = "192.168.253.1"
            mac = "543434"
            id = "%s_%s" % (source.id, address)
            ip_id = "foo"

        link = FakeNetworkLink()
        mock_get.return_value = link
        mock_remove.return_value = []
        ret = self.controller.delete(None, link.id)
        self.assertEqual([], ret)
        mock_get.assert_called_with(None, link.id)
        mock_remove.assert_called_with(None, link.mac)

    @mock.patch.object(helpers.OpenStackNeutron, "release_floating_ip")
    @mock.patch.object(network_link_api.Controller, "_get_interface_from_id")
    def test_delete_public(self, mock_get, mock_remove):
        class FakeNetworkLink(object):
            target = collections.namedtuple("Target", ["id"])("PUBLIC")
            source = collections.namedtuple("Source", ["id"])(uuid.uuid4().hex)
            address = "192.168.253.1"
            mac = "543434"
            id = "%s_%s" % (source.id, address)
            ip_id = "foo"

        link = FakeNetworkLink()
        mock_get.return_value = link
        mock_remove.return_value = []
        ret = self.controller.delete(None, link.id)
        self.assertEqual([], ret)
        mock_get.assert_called_with(None, link.id)
        mock_remove.assert_called_with(None, link.address)

    @mock.patch.object(helpers.OpenStackNeutron, "get_compute_net_link")
    def test_show(self, mock_get):
        os_link_list = fake_nets.network_links[fake_nets.tenants['foo']['id']]
        for os_link in os_link_list:
            mock_get.return_value = fake_nets.fake_build_link(
                os_link['network_id'], os_link['instance_id'], os_link['ip'],
                mac=None, pool=os_link['pool'], state=os_link['status']
            )
            link_id = '%s_%s_%s' % (
                os_link['instance_id'],
                os_link['network_id'],
                os_link['ip'])

            ret = self.controller.show(None, link_id)
            self.assertIsInstance(ret, os_network.OSNetworkInterface)
            self.assertEqual(os_link["ip"], ret.address)
            mock_get.assert_called_with(None, str(os_link['instance_id']),
                                        os_link['network_id'],
                                        os_link['ip'])

    def test_get_interface_from_id_invalid(self):
        self.assertRaises(exception.LinkNotFound,
                          self.controller._get_interface_from_id,
                          None,
                          "foobarbaz")

    def test_get_interface_from_id_invalid_no_matching_server(self):
        self.assertRaises(exception.LinkNotFound,
                          self.controller._get_interface_from_id,
                          None,
                          "%s_1.1.1.1" % uuid.uuid4().hex)

    @mock.patch.object(helpers.OpenStackNeutron, "get_compute_net_link")
    def test_get_interface_from_id(self, mock_get_server):
        server_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        server_addr = "1.1.1.1"
        link_id = "%s_%s_%s" % (server_id, net_id, server_addr)
        mock_get_server.return_value = fake_nets.fake_build_link(
            net_id, server_id, server_addr
        )
        ret = self.controller._get_interface_from_id(None, link_id)
        self.assertIsInstance(ret, os_network.OSNetworkInterface)
        mock_get_server.assert_called_with(None, server_id, net_id,
                                           server_addr)

    def test_get_network_link_resources_fixed(self):
        server_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        server_addr = "1.1.1.1"
        os_link = fake_nets.fake_build_link(
            net_id, server_id, server_addr
        )
        ret = network_link_api._get_network_link_resources([os_link])

        self.assertIsInstance(ret, list)
        self.assertIsInstance(ret[0], os_network.OSNetworkInterface)
        self.assertIsInstance(ret[0].source, compute.ComputeResource)
        self.assertIsInstance(ret[0].target, network.NetworkResource)
        self.assertEqual(ret[0].target.id, net_id)
        self.assertIsInstance(ret[0].ip_id, type(None))
        self.assertEqual(1, len(ret[0].mixins))
        self.assertIn(network_link.ip_network_interface, ret[0].mixins)

    def test_get_network_link_resources_public(self):
        server_id = uuid.uuid4().hex
        net_id = 'PUBLIC'
        server_addr = "1.1.1.1"
        os_link = fake_nets.fake_build_link(
            net_id, server_id, server_addr, pool='public'
        )
        ret = network_link_api._get_network_link_resources([os_link])

        self.assertIsInstance(ret, list)
        self.assertIsInstance(ret[0], os_network.OSNetworkInterface)
        self.assertIsInstance(ret[0].source, compute.ComputeResource)
        self.assertIsInstance(ret[0].target, network.NetworkResource)
        self.assertEqual(ret[0].target.id, net_id)
        self.assertIsInstance(ret[0].ip_id, type(None))
        self.assertEqual(2, len(ret[0].mixins))
        self.assertIn(network_link.ip_network_interface, ret[0].mixins)

    def test_get_network_link_resourcesinvalid(self):
        ret = network_link_api._get_network_link_resources(None)
        self.assertEqual(ret.__len__(), 0)

    @mock.patch.object(helpers.OpenStackNeutron, "assign_floating_ip")
    def test_create_public(self, mock_assign):
        server_id = uuid.uuid4().hex
        net_id = network_api.PUBLIC_NETWORK
        ip = '8.0.0.0'
        parameters = {
            "occi.core.target": net_id,
            "occi.core.source": server_id,
        }
        categories = {network_link.NetworkInterface.kind}
        req = fake_nets.create_req_test_occi(parameters, categories)
        mock_assign.return_value = fake_nets.fake_build_link(
            net_id, server_id, ip
        )
        ret = self.controller.create(req)
        self.assertIsNotNone(ret)
        link = ret.resources.pop()
        self.assertIsInstance(link, os_network.OSNetworkInterface)
        self.assertIsInstance(link.source, compute.ComputeResource)
        self.assertIsInstance(link.target, network.NetworkResource)
        self.assertEqual(net_id, link.target.id)
        self.assertEqual(server_id, link.source.id)

    @mock.patch.object(helpers.OpenStackNeutron, "create_port")
    def test_create_fixed(self, mock_cre_port):
        server_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        ip = '8.0.0.0'
        parameters = {
            "occi.core.target": net_id,
            "occi.core.source": server_id,
        }
        categories = {network_link.NetworkInterface.kind}
        req = fake_nets.create_req_test_occi(parameters, categories)
        mock_cre_port.return_value = fake_nets.fake_build_link(
            net_id, server_id, ip
        )
        ret = self.controller.create(req)
        self.assertIsNotNone(ret)
        link = ret.resources.pop()
        self.assertIsInstance(link, os_network.OSNetworkInterface)
        self.assertIsInstance(link.source, compute.ComputeResource)
        self.assertIsInstance(link.target, network.NetworkResource)
        self.assertEqual(net_id, link.target.id)
        self.assertEqual(server_id, link.source.id)
        mock_cre_port.assert_called_with(mock.ANY, parameters)

    @mock.patch.object(helpers.OpenStackNeutron, "create_port")
    def test_create_with_pool(self, mock_cre_port):
        server_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        ip = '8.0.0.0'
        parameters = {
            "occi.core.target": net_id,
            "occi.core.source": server_id,
        }
        pool = os_network.OSFloatingIPPool()
        categories = {network_link.NetworkInterface.kind, pool}
        req = fake_nets.create_req_test_occi(parameters, categories)
        mock_cre_port.return_value = fake_nets.fake_build_link(
            net_id, server_id, ip
        )
        ret = self.controller.create(req)
        self.assertIsNotNone(ret)
        link = ret.resources.pop()
        self.assertIsInstance(link, os_network.OSNetworkInterface)
        self.assertIsInstance(link.source, compute.ComputeResource)
        self.assertIsInstance(link.target, network.NetworkResource)
        self.assertEqual(net_id, link.target.id)
        self.assertEqual(server_id, link.source.id)

        mock_cre_port.assert_called_with(mock.ANY, parameters)
