# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
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

import uuid
import warnings

from oslo_config import cfg
import webob

from ooi.api import helpers
from ooi.tests import fakes_network as fakes
from ooi.tests.functional.middleware import test_middleware
from ooi import utils
from ooi import wsgi


class TestNetNeutronController(test_middleware.TestMiddleware):
    """Test OCCI network controller."""

    def setUp(self):
        super(TestNetNeutronController, self).setUp()
        self.schema = 'http://schemas.ogf.org/occi/infrastructure#network'
        self.accept = self.content_type = None
        self.application_url = fakes.application_url
        neutron_ooi_endpoint = "foo"

        def mock_endpoint(self, bar):
            if bar == "neutron_ooi_endpoint":
                return neutron_ooi_endpoint

        with mock.patch.object(cfg.ConfigOpts, "__getattr__",
                               side_effect=mock_endpoint,
                               autospec=True):
            self.app = wsgi.OCCIMiddleware(None)

    def assertExpectedResult(self, expected, result):
        expected = ["%s: %s" % e for e in expected]
        # NOTE(aloga): the order of the result does not matter
        results = str(result.text).splitlines()
        self.assertItemsEqual(expected, results)

    def test_deprecated_configuration(self):
        with warnings.catch_warnings(record=True) as w:
            neutron_endopoint = "/foo"
            warnings.simplefilter("always", DeprecationWarning)
            wsgi.OCCIMiddleware(None,
                                neutron_ooi_endpoint=neutron_endopoint)
            expected_message = (
                "Configuration of neutron_ooi_endpoint"
                " in api-paste.ini file is deprecated,"
                " include it in nova.conf")
            self.assertEqual(1, len(w))
            self.assertIs(DeprecationWarning,
                          w[-1].category)
            self.assertEqual(expected_message, w[-1].message.message)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_list_networks_empty(self, m):
        tenant = fakes.tenants["bar"]
        out = fakes.create_fake_json_resp(
            {"networks": fakes.networks[tenant['id']]}, 200)
        m.return_value.get_response.return_value = out

        req = self._build_req(path="/network",
                              tenant_id='X', method="GET")
        resp = req.get_response(self.app)

        self.assertEqual(204, resp.status_code)
        expected_result = ""
        self.assertExpectedResult(expected_result, resp)
        self.assertDefaults(resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_list_networks(self, m):
        tenant = fakes.tenants["foo"]
        out = fakes.create_fake_json_resp(
            {"networks": fakes.networks[tenant['id']]}, 200)
        m.return_value.get_response.return_value = out
        req = self._build_req(path="/network",
                              tenant_id='X', method="GET")
        resp = req.get_response(self.app)

        self.assertEqual(200, resp.status_code)
        expected = []
        for s in fakes.networks[tenant["id"]]:
            expected.append(
                ("X-OCCI-Location",
                 utils.join_url(self.application_url + "/",
                                "network/%s" % s["id"]))
            )
        self.assertDefaults(resp)
        self.assertExpectedResult(expected, resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_create(self, m):
        tenant = fakes.tenants["foo"]
        net_out = fakes.create_fake_json_resp(
            {"network": fakes.networks[tenant['id']][0]}, 200)
        mock_net = mock.Mock(webob.Request)
        mock_net.get_response.return_value = net_out
        subnet_out = fakes.create_fake_json_resp(
            {"subnet": fakes.networks[tenant['id']][0]["subnet_info"]},
            200)
        mock_subnet = mock.Mock(webob.Request)
        mock_subnet.get_response.return_value = subnet_out
        public_out = fakes.create_fake_json_resp(
            {"networks": fakes.networks[tenant['id']]},
            200)

        mock_public = mock.Mock(webob.Request)
        mock_public.get_response.return_value = public_out
        router_out = fakes.create_fake_json_resp(
            {"router": {"id": uuid.uuid4().hex}},
            200)
        mock_router = mock.Mock(webob.Request)
        mock_router.get_response.return_value = router_out
        mock_iface = mock.Mock(webob.Request)
        mock_iface.get_response.return_value = fakes.create_fake_json_resp(
            {"foo": "foo"}, 200)
        m.side_effect = [mock_net, mock_subnet, mock_public,
                         mock_router, mock_iface
                         ]
        name = fakes.networks[tenant["id"]][0]["name"]
        net_id = fakes.networks[tenant["id"]][0]["id"]
        address = fakes.networks[tenant["id"]][0]["subnet_info"]["cidr"]
        headers = {
            'Category': 'network;'
                        ' scheme='
                        '"http://schemas.ogf.org/occi/infrastructure#";'
                        'class="kind",'
                        'ipnetwork;'
                        ' scheme='
                        '"http://schemas.ogf.org/occi/infrastructure/'
                        'network#";'
                        'class="mixin",',
            'X-OCCI-Attribute': '"occi.core.title"="%s",'
                                '"occi.network.address"="%s"' %
                                (name, address)
        }
        req = self._build_req(path="/network",
                              tenant_id='X',
                              method="POST",
                              headers=headers)

        m.return_value = fakes.networks[tenant['id']][0]
        resp = req.get_response(self.app)
        self.assertEqual(200, resp.status_code)
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "network/%s" % net_id))]
        self.assertExpectedResult(expected, resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_show_networks(self, m):
        tenant = fakes.tenants["foo"]

        for n in fakes.networks[tenant["id"]]:
            net_out = fakes.create_fake_json_resp(
                {"network": n}, 200)
            mock_net = mock.Mock(webob.Request)
            mock_net.get_response.return_value = net_out
            subnet_out = fakes.create_fake_json_resp(
                {"subnet": n["subnet_info"]}, 200)
            mock_subnet = mock.Mock(webob.Request)
            mock_subnet.get_response.return_value = subnet_out
            m.side_effect = [mock_net, mock_subnet]

            req = self._build_req(path="/network/%s" % n["id"],
                                  tenant_id='X',
                                  method="GET")
            resp = req.get_response(self.app)
            expected = fakes.build_occi_network(n)
            self.assertEqual(200, resp.status_code)
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_delete_networks(self, m):
        tenant = fakes.tenants["foo"]
        port_out = fakes.create_fake_json_resp(
            {"ports": fakes.ports[tenant['id']]}, 200)
        mock_port = mock.Mock(webob.Request)
        mock_port.get_response.return_value = port_out
        empty_out = fakes.create_fake_json_resp([], 204)
        mock_empty = mock.Mock(webob.Request)
        mock_empty.get_response.return_value = empty_out
        m.side_effect = [mock_port, mock_empty, mock_empty,
                         mock_empty, mock_empty]
        for n in fakes.networks[tenant["id"]]:
            m.return_value = fakes.create_fake_json_resp(
                {"subnet": n["subnet_info"]}, 200)
            req = self._build_req(path="/network/%s" % n["id"],
                                  tenant_id='X',
                                  method="DELETE")
            resp = req.get_response(self.app)
            self.assertEqual(204, resp.status_code)
            self.assertDefaults(resp)


class NetworkNeutronTextPlain(test_middleware.TestMiddlewareTextPlain,
                              TestNetNeutronController):
    """Test OCCI network controller with Accept: text/plain."""


class NetworklNeutronTextOcci(test_middleware.TestMiddlewareTextOcci,
                              TestNetNeutronController):
    """Test OCCI network controller with Accept: text/occi."""


class TestNetNovaController(test_middleware.TestMiddleware):
    """Test OCCI network controller."""

    def setUp(self):
        super(TestNetNovaController, self).setUp()
        self.schema = 'http://schemas.ogf.org/occi/infrastructure#network'
        self.accept = self.content_type = None
        self.application_url = fakes.application_url
        self.app = wsgi.OCCIMiddleware(None)

    def assertExpectedResult(self, expected, result):
        expected = ["%s: %s" % e for e in expected]
        # NOTE(aloga): the order of the result does not matter
        results = str(result.text).splitlines()
        self.assertItemsEqual(expected, results)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_list_networks_empty(self, m):
        tenant = fakes.tenants["bar"]
        out = fakes.create_fake_json_resp(
            {"networks": fakes.networks_nova[tenant['id']]}, 200)
        m.return_value.get_response.return_value = out

        req = self._build_req(path="/network",
                              tenant_id='X', method="GET")
        resp = req.get_response(self.app)

        self.assertEqual(204, resp.status_code)
        expected_result = ""
        self.assertExpectedResult(expected_result, resp)
        self.assertDefaults(resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_list_networks(self, m):
        tenant = fakes.tenants["foo"]
        out = fakes.create_fake_json_resp(
            {"networks": fakes.networks_nova[tenant['id']]}, 200)
        m.return_value.get_response.return_value = out
        req = self._build_req(path="/network",
                              tenant_id='X', method="GET")
        resp = req.get_response(self.app)

        self.assertEqual(200, resp.status_code)
        expected = []
        for s in fakes.networks_nova[tenant["id"]]:
            expected.append(
                ("X-OCCI-Location",
                 utils.join_url(self.application_url + "/",
                                "network/%s" % s["id"]))
            )
        self.assertDefaults(resp)
        self.assertExpectedResult(expected, resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_create(self, m):
        tenant = fakes.tenants["foo"]
        net_out = fakes.create_fake_json_resp(
            {"network": fakes.networks_nova[tenant['id']][0]}, 200)
        mock_net = mock.Mock(webob.Request)
        mock_net.get_response.return_value = net_out
        m.side_effect = [mock_net]
        name = fakes.networks_nova[tenant["id"]][0]["label"]
        net_id = fakes.networks_nova[tenant["id"]][0]["id"]
        address = fakes.networks_nova[tenant["id"]][0]["cidr"]
        headers = {
            'Category': 'network;'
                        ' scheme='
                        '"http://schemas.ogf.org/occi/infrastructure#";'
                        'class="kind",'
                        'ipnetwork;'
                        ' scheme='
                        '"http://schemas.ogf.org/occi/'
                        'infrastructure/network#";'
                        'class="mixin",',
            'X-OCCI-Attribute': '"occi.core.title"="%s",'
                                '"occi.network.address"="%s"' %
                                (name, address)
        }
        req = self._build_req(path="/network",
                              tenant_id='X',
                              method="POST",
                              headers=headers)

        m.return_value = fakes.networks_nova[tenant['id']][0]
        resp = req.get_response(self.app)
        self.assertEqual(200, resp.status_code)
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "network/%s" % net_id))]
        self.assertExpectedResult(expected, resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_show_networks(self, m):
        tenant = fakes.tenants["foo"]

        for n in fakes.networks_nova[tenant["id"]]:
            net_out = fakes.create_fake_json_resp(
                {"network": n}, 200)
            mock_net = mock.Mock(webob.Request)
            mock_net.get_response.return_value = net_out
            m.side_effect = [mock_net]

            req = self._build_req(path="/network/%s" % n["id"],
                                  tenant_id='X',
                                  method="GET")
            resp = req.get_response(self.app)
            expected = fakes.build_occi_nova(n)
            self.assertEqual(200, resp.status_code)
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)

    @mock.patch.object(helpers.BaseHelper, "_get_req")
    def test_delete_networks(self, m):
        tenant = fakes.tenants["foo"]
        empty_out = fakes.create_fake_json_resp(
            [], 204)
        mock_empty = mock.Mock(webob.Request)
        mock_empty.get_response.return_value = empty_out
        for n in fakes.networks_nova[tenant["id"]]:
            m.side_effect = [mock_empty]
            req = self._build_req(path="/network/%s" % n["id"],
                                  tenant_id='X',
                                  method="DELETE")
            resp = req.get_response(self.app)
            self.assertEqual(204, resp.status_code)
            self.assertDefaults(resp)

    def test_action_net(self):
        tenant = fakes.tenants["foo"]

        for action in ("up", "down"):
            headers = {
                'Category': (
                    '%s;'
                    'scheme="http://schemas.ogf.org/occi/infrastructure/'
                    'network/action#";'
                    'class="action"' % action)
            }
            for net in fakes.networks[tenant["id"]]:
                req = self._build_req("/network/%s?action=%s" % (net["id"],
                                                                 action),
                                      tenant_id=tenant["id"], method="POST",
                                      headers=headers)
                resp = req.get_response(self.app)
                self.assertDefaults(resp)
                self.assertEqual(501, resp.status_code)

    def test_invalid_action(self):
        tenant = fakes.tenants["foo"]

        action = "foo"
        for net in fakes.networks[tenant["id"]]:
            req = self._build_req("/network/%s?action=%s" % (net["id"],
                                                             action),
                                  tenant["id"], method="POST")
            resp = req.get_response(self.app)
            self.assertDefaults(resp)
            self.assertEqual(400, resp.status_code)


class NetworkNovaControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                     TestNetNovaController):
    """Test OCCI network controller with Accept: text/plain."""


class NetworkNovaControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                    TestNetNovaController):
    """Test OCCI network controller with Accept: text/occi."""
