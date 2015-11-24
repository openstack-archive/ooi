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

import uuid

import mock

from ooi.api import helpers
from ooi.api import network as network_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import network
from ooi.tests import base
from ooi.tests import fakes


class TestController(base.TestController):
    def setUp(self):
        super(TestController, self).setUp()
        self.controller = network_api.Controller(mock.MagicMock(), None)

    @mock.patch("ooi.api.network._build_network")
    @mock.patch.object(network_api.Controller, "_floating_index")
    def test_index(self, m_float, m_build):
        res = network.NetworkResource(title="foo",
                                      id="foo",
                                      state="active",
                                      mixins=[network.ip_network])
        res_fixed = network.NetworkResource(title="fixed",
                                            id="fixed",
                                            state="active",
                                            mixins=[network.ip_network])

        m_float.return_value = [res]
        m_build.return_value = res_fixed
        ret = self.controller.index(None)
        self.assertIsInstance(ret, collection.Collection)
        self.assertEqual([res, res_fixed], ret.resources)
        m_float.assert_called_with(None)
        m_build.assert_called_with("fixed")

    def test_build(self):
        ret = network_api._build_network("foo")
        self.assertIsInstance(ret, network.NetworkResource)
        self.assertEqual("foo", ret.title)
        self.assertEqual("foo", ret.id)
        self.assertEqual([network.ip_network], ret.mixins)

    def test_build_with_prefix(self):
        ret = network_api._build_network("foo", prefix="bar")
        self.assertIsInstance(ret, network.NetworkResource)
        self.assertEqual("foo", ret.title)
        self.assertEqual("bar/foo", ret.id)
        self.assertEqual([network.ip_network], ret.mixins)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_show(self, m_pools):
        for tenant in fakes.tenants.values():
            pools = fakes.pools[tenant["id"]]
            if not pools:
                continue
            m_pools.return_value = pools
            ret = self.controller.show(None, "floating")[0]
            self.assertIsInstance(ret, network.NetworkResource)
            self.assertEqual("floating", ret.title)
            self.assertEqual("floating", ret.id)
            self.assertEqual([network.ip_network], ret.mixins)
            m_pools.assert_called_with(None)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_show_not_found(self, m_pools):
        tenant = fakes.tenants["foo"]
        pools = fakes.pools[tenant["id"]]
        m_pools.return_value = pools
        self.assertRaises(exception.NetworkNotFound,
                          self.controller.show,
                          None, uuid.uuid4().hex)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_show_empty_floating(self, m_pools):
        m_pools.return_value = []
        self.assertRaises(exception.NetworkNotFound,
                          self.controller.show,
                          None, "floating")
        m_pools.assert_called_with(None)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_show_non_existent(self, m_pools):
        m_pools.return_value = []
        self.assertRaises(exception.NetworkNotFound,
                          self.controller.show,
                          None, None)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_floating_ips(self, m_pools):
        for tenant in fakes.tenants.values():
            pools = fakes.pools[tenant["id"]]
            m_pools.return_value = pools
            ret = self.controller._floating_index(None)
            if pools:
                self.assertEqual(1, len(ret))
                self.assertIsInstance(ret[0], network.NetworkResource)
                self.assertEqual("floating", ret[0].title)
                self.assertEqual("floating", ret[0].id)
            else:
                self.assertEqual(0, len(ret))
            m_pools.assert_called_with(None)
