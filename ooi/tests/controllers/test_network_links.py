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
import webob

from ooi.api import helpers
from ooi.api import network_link as network_link_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.openstack import network as os_network
from ooi.tests import base
from ooi.tests import fakes


class TestNetworkLinkController(base.TestController):
    def setUp(self):
        super(TestNetworkLinkController, self).setUp()
        self.controller = network_link_api.Controller(mock.MagicMock(), None)

    def _build_req(self, tenant_id, path="/whatever", **kwargs):
        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}

        kwargs["base_url"] = self.application_url

        return webob.Request.blank(path, environ=environ, **kwargs)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ips")
    def test_index(self, mock_floating_ips):
        for tenant in fakes.tenants.values():
            ips = fakes.floating_ips[tenant["id"]]
            mock_floating_ips.return_value = ips
            ret = self.controller.index(None)
            self.assertIsInstance(ret, collection.Collection)
            if tenant["name"] == "baz":
                for idx, ip in enumerate(ips):
                    if ip["instance_id"]:
                        self.assertIsInstance(ret.resources[idx],
                                              os_network.OSNetworkInterface)
            else:
                self.assertEqual([], ret.resources)
            mock_floating_ips.assert_called_with(None)

    @mock.patch.object(network_link_api.Controller, "_get_interface_from_id")
    def test_delete_invalid(self, mock_get):
        class FakeNetworkLink(object):
            target = collections.namedtuple("Target", ["id"])("fixed")

        server_id = uuid.uuid4().hex
        server_addr = "192.168.253.1"
        link_id = "%s_%s" % (server_id, server_addr)
        mock_get.return_value = FakeNetworkLink()
        self.assertRaises(exception.Invalid,
                          self.controller.delete, None, link_id)
        mock_get.assert_called_with(None, link_id)

    @mock.patch.object(helpers.OpenStackHelper, "release_floating_ip")
    @mock.patch.object(helpers.OpenStackHelper, "remove_floating_ip")
    @mock.patch.object(network_link_api.Controller, "_get_interface_from_id")
    def test_delete(self, mock_get, mock_remove, mock_release):
        class FakeNetworkLink(object):
            target = collections.namedtuple("Target", ["id"])("floating")
            source = collections.namedtuple("Source", ["id"])(uuid.uuid4().hex)
            address = "192.168.253.1"
            id = "%s_%s" % (source.id, address)
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

    @mock.patch.object(network_link_api.Controller, "_get_interface_from_id")
    def test_show(self, mock_get):
        mock_get.return_value = "foo"

        ret = self.controller.show(None, "bar")
        self.assertEqual(["foo"], ret)
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

    @mock.patch.object(network_link_api.Controller, "_get_os_network_ip")
    @mock.patch.object(helpers.OpenStackHelper, "get_server")
    def test_get_interface_from_id(self, mock_get_server, mock_get_ip):
        server_id = uuid.uuid4().hex
        server_addr = "1.1.1.1"
        link_id = "%s_%s" % (server_id, server_addr)
        c = compute.ComputeResource(title="Compute", id=server_id)

        mock_get_server.return_value = {"addresses": {"foo": [
            {"addr": server_addr}]}}
        mock_get_ip.return_value = ("bar", "baz")

        a = os_network.OSNetworkInterface(c, "bar", "mac", server_addr, "baz")
        ret = self.controller._get_interface_from_id(None, link_id)

        self.assertIsInstance(ret, os_network.OSNetworkInterface)
        self.assertEqual(a.ip_id, ret.ip_id)
        self.assertEqual(c.id, ret.source.id)

        mock_get_server.assert_called_with(None, server_id)
        mock_get_ip.assert_called_with(None, {"addr": server_addr})

    def test_get_os_network_ip_fixed(self):
        addr = {"addr": "1.1.1.1",
                "OS-EXT-IPS:type": "fixed",
                "OS-EXT-IPS-MAC:mac_addr": "1234"}
        ret = self.controller._get_os_network_ip(None, addr)
        self.assertIsInstance(ret, tuple)
        self.assertIsInstance(ret[0], network.NetworkResource)
        self.assertIsInstance(ret[1], type(None))

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ips")
    def test_get_os_network_ip(self, mock_floating_ips):
        ips = fakes.floating_ips[fakes.tenants["baz"]["id"]]
        for ip in ips:
            addr = {"addr": ip["ip"],
                    "OS-EXT-IPS:type": "floating",
                    "OS-EXT-IPS-MAC:mac_addr": "1234"}
            mock_floating_ips.return_value = ips

            ret = self.controller._get_os_network_ip(None, addr)
            self.assertIsInstance(ret, tuple)
            self.assertIsInstance(ret[0], network.NetworkResource)
            self.assertEqual(ip["id"], ret[1])

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ips")
    def test_get_os_network_ip_invalid(self, mock_floating_ips):
        addr = {"addr": "1.1.1.1",
                "OS-EXT-IPS:type": "floating",
                "OS-EXT-IPS-MAC:mac_addr": "1234"}
        for tenant in fakes.tenants.values():
            ips = fakes.floating_ips[tenant["id"]]
            mock_floating_ips.return_value = ips
            self.assertRaises(exception.NetworkNotFound,
                              self.controller._get_os_network_ip,
                              None,
                              addr)

    @mock.patch("ooi.occi.validator.Validator")
    def test_create_invalid(self, mock_validator):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        net_id = "fixed"
        server_id = uuid.uuid4().hex
        obj = {
            "attributes": {
                "occi.core.target": net_id,
                "occi.core.source": server_id,
            }
        }

        req.get_parser = mock.MagicMock()
        req.get_parser.return_value.return_value.parse.return_value = obj
        mock_validator.validate.return_value = True
        self.assertRaises(exception.Invalid,
                          self.controller.create, req, None)

    @mock.patch("ooi.occi.validator.Validator")
    def test_create_invalid_net_id(self, mock_validator):
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
        req.get_parser.return_value.return_value.parse.return_value = obj
        mock_validator.validate.return_value = True
        self.assertRaises(exception.NetworkPoolFound,
                          self.controller.create, req, None)

    @mock.patch.object(helpers.OpenStackHelper, "associate_floating_ip")
    @mock.patch.object(helpers.OpenStackHelper, "allocate_floating_ip")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create(self, mock_validator, mock_allocate, mock_associate):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        pool_name = "public"
        net_id = '/'.join(["floating", pool_name])
        server_id = uuid.uuid4().hex
        obj = {
            "attributes": {
                "occi.core.target": net_id,
                "occi.core.source": server_id,
            }
        }
        ips = fakes.floating_ips[fakes.tenants["baz"]["id"]]

        for ip in ips:
            req.get_parser = mock.MagicMock()
            req.get_parser.return_value.return_value.parse.return_value = obj
            mock_validator.validate.return_value = True
            mock_allocate.return_value = ip
            mock_associate.return_value = None

            ret = self.controller.create(req, None)
            link = ret.resources.pop()
            self.assertIsInstance(link, os_network.OSNetworkInterface)
            self.assertIsInstance(link.source, compute.ComputeResource)
            self.assertIsInstance(link.target, network.NetworkResource)
            self.assertEqual(net_id, link.target.id)
            self.assertEqual(server_id, link.source.id)

            mock_allocate.assert_called_with(mock.ANY, pool_name)
            mock_associate.assert_called_with(mock.ANY, server_id, ip["id"])
