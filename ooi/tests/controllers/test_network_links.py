# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
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
from ooi.api import network_link as network_link_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.openstack import network as os_network
from ooi.tests import base
from ooi.tests import fakes
from ooi.tests import fakes_network as fake_nets


class TestNetworkLinkController(base.TestController):
    def setUp(self):
        super(TestNetworkLinkController, self).setUp()
        self.controller = network_link_api.Controller(mock.MagicMock(), None)

    @mock.patch.object(helpers.OpenStackHelper, "list_compute_net_links")
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

    @mock.patch.object(helpers.OpenStackHelper, "list_compute_net_links")
    def test_index_Empty(self, mock_list):
        req = fake_nets.create_req_test(None, None)
        links = []
        mock_list.return_value = links
        ret = self.controller.index(req)
        self.assertIsInstance(ret, collection.Collection)
        self.assertEqual(ret.resources.__len__(), 0)

    @mock.patch.object(helpers.OpenStackHelper,
                       "delete_port")
    @mock.patch.object(network_link_api.Controller,
                       "_get_interface_from_id")
    def test_delete_fixed(self, mock_get, mock_delete):
        net_id = uuid.uuid4().hex
        server_id = uuid.uuid4().hex
        server_addr = "192.168.253.1"
        link_id = "%s_%s_%s" % (
            server_id, net_id, server_addr)
        ip_ident = uuid.uuid4().hex

        class FakeNetworkLink(object):
            target = collections.namedtuple("Target", ["id"])(net_id)
            source = collections.namedtuple("Source", ["id"])(server_id)
            address = server_addr
            mac = 'foo'
            id = link_id
            ip_id = ip_ident

        mock_get.return_value = FakeNetworkLink()
        mock_delete.return_value = []
        ret = self.controller.delete(None, link_id)
        self.assertEqual([], ret)
        mock_get.assert_called_with(None, link_id)
        mock_delete.assert_called_with(None, server_id, ip_ident)

    @mock.patch.object(helpers.OpenStackHelper, "release_floating_ip")
    @mock.patch.object(helpers.OpenStackHelper, "remove_floating_ip")
    @mock.patch.object(network_link_api.Controller, "_get_interface_from_id")
    def test_delete_public(self, mock_get, mock_remove, mock_release):
        net_id = "PUBLIC"
        server_id = uuid.uuid4().hex
        server_addr = "192.168.253.1"
        link_id = "%s_%s_%s" % (server_id, net_id, server_addr)
        mac_id = uuid.uuid4().hex

        class FakeNetworkLink(object):
            target = collections.namedtuple("Target", ["id"])(net_id)
            source = collections.namedtuple("Source", ["id"])(server_id)
            address = server_addr
            mac = mac_id
            id = link_id
            ip_id = "foo"

        link = FakeNetworkLink()
        mock_get.return_value = link
        mock_release.return_value = None
        mock_remove.return_value = None

        ret = self.controller.delete(None, link.id)
        self.assertEqual([], ret)

        mock_get.assert_called_with(None, link.id)
        mock_remove.assert_called_with(None, link.source.id, link.address)
        mock_release.assert_called_with(None, link.ip_id)

    @mock.patch.object(helpers.OpenStackHelper, "get_compute_net_link")
    def test_show_complete(self, mock_get):
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

    @mock.patch.object(network_link_api.Controller, "_get_interface_from_id")
    def test_show(self, mock_get):
        mock_get.return_value = "foo"

        ret = self.controller.show(None, "bar")
        self.assertEqual("foo", ret)
        mock_get.assert_called_with(None, "bar")

    def test_get_interface_from_id_invalid(self):
        self.assertRaises(exception.LinkNotFound,
                          self.controller._get_interface_from_id,
                          None,
                          "foobarbaz")

    @mock.patch.object(helpers.OpenStackHelper, "get_server")
    def test_get_interface_from_id_invalid_no_matching_server(self, mock_get):
        mock_get.return_value = {"addresses": {"foo": [{"addr": "1.1.1.2"}]}}

        self.assertRaises(exception.LinkNotFound,
                          self.controller._get_interface_from_id,
                          None,
                          "%s_1.1.1.1" % uuid.uuid4().hex)

    @mock.patch.object(helpers.OpenStackHelper, "get_compute_net_link")
    def test_get_interface_from_id(self, mock_get_server):
        server_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        server_addr = "1.1.1.1"
        link_id = "%s_%s_%s" % (server_id, net_id, server_addr)
        mock_get_server.return_value = fake_nets.fake_build_link(
            net_id, server_id, server_addr
        )
        ret = self.controller.show(None, link_id)
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
        has_pool = False
        for m in ret[0].mixins:
            if isinstance(m, os_network.OSFloatingIPPool):
                has_pool = True
                break
        self.assertTrue(has_pool)

    def test_get_network_link_resources_empty(self):
        ret = network_link_api._get_network_link_resources(None)
        self.assertEqual(ret.__len__(), 0)

    @mock.patch.object(helpers.OpenStackHelper, "assign_floating_ip")
    @mock.patch("ooi.api.helpers.get_id_with_kind")
    def test_create_public(self, mock_get_id, mock_assign):
        server_id = uuid.uuid4().hex
        net_id = "PUBLIC"
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
        mock_get_id.side_effect = [('', net_id), ('', server_id)]
        ret = self.controller.create(req)
        self.assertIsNotNone(ret)
        link = ret.resources.pop()
        self.assertIsInstance(link, os_network.OSNetworkInterface)
        self.assertIsInstance(link.source, compute.ComputeResource)
        self.assertIsInstance(link.target, network.NetworkResource)
        self.assertEqual(net_id, link.target.id)
        self.assertEqual(server_id, link.source.id)
        mock_assign.assert_called_with(mock.ANY, net_id, server_id, None)

    @mock.patch.object(helpers.OpenStackHelper, "create_port")
    @mock.patch("ooi.api.helpers.get_id_with_kind")
    def test_create_fixed(self, mock_get_id, mock_cre_port):
        server_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        mock_get_id.side_effect = [('', net_id), ('', server_id)]
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
        mock_cre_port.assert_called_with(mock.ANY, net_id, server_id)

    @mock.patch("ooi.api.helpers.get_id_with_kind")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_invalid_ids(self, mock_validator, mock_get_id):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        net_id = "foobarbaz"
        server_id = uuid.uuid4().hex
        obj = {
            "attributes": {
                "occi.core.target": net_id,
                "occi.core.source": server_id,
            }
        }

        req.get_parser = mock.MagicMock()
        mock_get_id.side_effect = exception.Invalid()
        req.get_parser.return_value.return_value.parse.return_value = obj
        mock_validator.validate.return_value = True
        self.assertRaises(exception.Invalid,
                          self.controller.create, req, None)

    @mock.patch.object(helpers.OpenStackHelper, "associate_floating_ip")
    @mock.patch.object(helpers.OpenStackHelper, "allocate_floating_ip")
    @mock.patch("ooi.api.helpers.get_id_with_kind")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_no_pool(self, mock_validator, mock_get_id, mock_allocate,
                            mock_associate):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        net_id = "PUBLIC"
        server_id = uuid.uuid4().hex
        obj = {
            "attributes": {
                "occi.core.target": net_id,
                "occi.core.source": server_id,
            },
            "schemes": {
            }
        }
        ips = fakes.floating_ips[fakes.tenants["baz"]["id"]]

        for ip in ips:
            req.get_parser = mock.MagicMock()
            req.get_parser.return_value.return_value.parse.return_value = obj
            mock_validator.validate.return_value = True
            mock_allocate.return_value = ip
            mock_associate.return_value = None
            mock_get_id.side_effect = [('', net_id), ('', server_id)]

            ret = self.controller.create(req, None)
            link = ret.resources.pop()
            self.assertIsInstance(link, os_network.OSNetworkInterface)
            self.assertIsInstance(link.source, compute.ComputeResource)
            self.assertIsInstance(link.target, network.NetworkResource)
            self.assertEqual(net_id, link.target.id)
            self.assertEqual(server_id, link.source.id)

            mock_allocate.assert_called_with(mock.ANY, None)
            mock_associate.assert_called_with(mock.ANY, server_id, ip["ip"])

    @mock.patch.object(helpers.OpenStackHelper, "associate_floating_ip")
    @mock.patch.object(helpers.OpenStackHelper, "allocate_floating_ip")
    @mock.patch("ooi.api.helpers.get_id_with_kind")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_with_pool(self, mock_validator, mock_get_id, mock_allocate,
                              mock_associate):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        net_id = "PUBLIC"
        server_id = uuid.uuid4().hex
        pool_name = "public"
        obj = {
            "attributes": {
                "occi.core.target": net_id,
                "occi.core.source": server_id,
            },
            "schemes": {
                os_network.OSFloatingIPPool.scheme: [pool_name],
            }
        }
        ips = fakes.floating_ips[fakes.tenants["baz"]["id"]]

        for ip in ips:
            req.get_parser = mock.MagicMock()
            req.get_parser.return_value.return_value.parse.return_value = obj
            mock_validator.validate.return_value = True
            mock_allocate.return_value = ip
            mock_associate.return_value = None
            mock_get_id.side_effect = [('', net_id), ('', server_id)]

            ret = self.controller.create(req, None)
            link = ret.resources.pop()
            self.assertIsInstance(link, os_network.OSNetworkInterface)
            self.assertIsInstance(link.source, compute.ComputeResource)
            self.assertIsInstance(link.target, network.NetworkResource)
            self.assertEqual(net_id, link.target.id)
            self.assertEqual(server_id, link.source.id)

            mock_allocate.assert_called_with(mock.ANY, pool_name)
            mock_associate.assert_called_with(mock.ANY, server_id, ip["ip"])
