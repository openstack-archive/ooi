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
import webob

from ooi.api import helpers
from ooi.api import network as network_api
from ooi.occi.core import collection
from ooi.occi.infrastructure import network
from ooi.tests.controllers import base
from ooi.tests import fakes


class TestNetworkController(base.TestController):
    def setUp(self):
        super(TestNetworkController, self).setUp()
        self.controller = network_api.NetworkController(mock.MagicMock(), None)

    def _build_req(self, tenant_id, path="/whatever", **kwargs):
        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}

        kwargs["base_url"] = self.application_url

        return webob.Request.blank(path, environ=environ, **kwargs)

    @mock.patch.object(network_api.NetworkController, "_floating_index")
    def test_index(self, m_float):
        res = network.NetworkResource(title="foo",
                                      id="foo",
                                      state="active",
                                      mixins=[network.ip_network])

        m_float.return_value = [res]
        ret = self.controller.index(None)
        self.assertIsInstance(ret, collection.Collection)
        self.assertEqual(res, ret.resources[0])
        m_float.assert_called_with(None)

    @mock.patch("ooi.api.network._build_network")
    @mock.patch.object(network_api.NetworkController, "_floating_index")
    def test_general_index(self, m_float, m_build):
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
        ret = self.controller.general_index(None)
        self.assertIsInstance(ret, collection.Collection)
        self.assertEqual([res, res_fixed], ret.resources)
        m_float.assert_called_with(None)
        m_build.assert_called_with("fixed")

    def test_fixed(self):
        ret = self.controller.show_fixed(None)
        self.assertIsInstance(ret, network.NetworkResource)
        self.assertEqual("fixed", ret.title)
        self.assertEqual("fixed", ret.id)
        self.assertEqual([network.ip_network], ret.mixins)

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
            m_pools.return_value = pools
            for idx, pool in enumerate(pools):
                pool = pools[0]
                ret = self.controller.show(None, pool["name"])[0]
                self.assertIsInstance(ret, network.NetworkResource)
                self.assertEqual(pool["name"], ret.title)
                self.assertEqual("%s/%s" % (network_api.FLOATING_PREFIX,
                                            pool["name"]), ret.id)
                self.assertEqual([network.ip_network], ret.mixins)
                m_pools.assert_called_with(None)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_show_not_found(self, m_pools):
        tenant = fakes.tenants["foo"]
        pools = fakes.pools[tenant["id"]]
        m_pools.return_value = pools
        self.assertRaises(webob.exc.HTTPNotFound,
                          self.controller.show,
                          None, uuid.uuid4().hex)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_show_empty(self, m_pools):
        m_pools.return_value = []
        self.assertRaises(webob.exc.HTTPNotFound,
                          self.controller.show,
                          None, None)
        m_pools.assert_called_with(None)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_floating_ips(self, m_pools):
        for tenant in fakes.tenants.values():
            pools = fakes.pools[tenant["id"]]
            m_pools.return_value = pools
            ret = self.controller._floating_index(None)
            self.assertEqual(len(pools), len(ret))
            for idx, el in enumerate(ret):
                self.assertIsInstance(el, network.NetworkResource)
                self.assertEqual(pools[idx]["name"], el.title)
                self.assertEqual("%s/%s" % (network_api.FLOATING_PREFIX,
                                            pools[idx]["name"]), el.id)

            m_pools.assert_called_with(None)
