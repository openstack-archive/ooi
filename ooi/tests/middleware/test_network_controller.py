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

import mock

from ooi.api import helpers_neutron
from ooi.api import network
from ooi.occi.core import collection
from ooi.tests import fakes_network as fakes
from ooi.tests.middleware import test_middleware
from ooi import utils
from ooi import wsgi


def create_occi_results(data):
    return network.Controller(None)._get_network_resources(data)


class TestMiddlewareNeutron(test_middleware.TestMiddleware):
    """OCCI middleware test for Neutron middleware.

    According to the OCCI HTTP rendering, no Accept header
    means text/plain.
    """
    def setUp(self):
        super(TestMiddlewareNeutron, self).setUp()
        self.accept = self.content_type = None
        self.application_url = fakes.application_url
        self.app = wsgi.OCCIMiddleware(None)


class TestNetworkController(TestMiddlewareNeutron):
    """Test OCCI compute controller."""

    def setUp(self):
        super(TestNetworkController, self).setUp()

    def assertExpectedResult(self, expected, result):
        expected = ["%s: %s" % e for e in expected]
        # NOTE(aloga): the order of the result does not matter
        results = str(result.text).splitlines()
        self.assertItemsEqual(expected, results)

    @mock.patch.object(network.Controller, "index")
    def test_list_networks_empty(self, m):
        tenant = fakes.tenants["bar"]
        headers = {
            'Category': 'network; scheme="http://schema#";class="kind";',
            'X_OCCI_Attribute': 'project=%s' % tenant["id"],
        }
        url = "/network"
        req = self._build_req(path=url,
                              tenant_id='X',
                              method="GET",
                              headers=headers, content_type="text/occi")
        m.return_value = collection.Collection(
            create_occi_results(fakes.networks[tenant['id']]))
        resp = req.get_response(self.app)
        self.assertEqual(204, resp.status_code)
        expected_result = ""
        self.assertExpectedResult(expected_result, resp)
        self.assertDefaults(resp)

    @mock.patch.object(network.Controller, "index")
    def test_list_networks(self, m):
        tenant = fakes.tenants["foo"]
        ooi_net = helpers_neutron.OpenStackNeutron._build_networks(
            fakes.networks[tenant['id']]
        )
        m.return_value = collection.Collection(
            create_occi_results(ooi_net))
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

    @mock.patch.object(network.Controller, "create")
    def test_create(self, m):
        tenant = fakes.tenants["foo"]
        headers = {
            'Category': 'network; scheme="http://schema#";class="kind",' +
                        'mixinID;'
                        'scheme="http://schemas.openstack.org/template/os#";'
                        ' class=mixin',
            'X_Occi_Attribute': 'project=%s' % tenant["id"],
        }
        req = self._build_req(path="/network",
                              tenant_id='X',
                              method="POST",
                              headers=headers)
        fake_net = fakes.fake_network_occi(
            fakes.networks[tenant['id']]
        )[0]
        m.return_value = collection.Collection([fake_net])
        resp = req.get_response(self.app)
        self.assertEqual(200, resp.status_code)
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "network/%s" % fake_net.id))]
        self.assertExpectedResult(expected, resp)

    @mock.patch.object(network.Controller, "show")
    def test_show_networks(self, m):
        tenant = fakes.tenants["foo"]

        for n in fakes.networks[tenant["id"]]:
            ooi_net = helpers_neutron.OpenStackNeutron._build_networks([n])[0]
            m.return_value = create_occi_results([ooi_net])[0]
            req = self._build_req(path="/network/%s" % n["id"],
                                  tenant_id='X',
                                  method="GET")
            resp = req.get_response(self.app)
            expected = fakes.build_occi_network(n)
            self.assertEqual(200, resp.status_code)
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)

    @mock.patch.object(network.Controller, "delete")
    def test_delete_networks(self, m):
        tenant = fakes.tenants["foo"]
        for n in fakes.networks[tenant["id"]]:
            m.return_value = create_occi_results([])
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


class NetworkControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                 TestNetworkController):
    """Test OCCI network controller with Accept: text/plain."""


class NetworkControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                TestNetworkController):
    """Test OCCI network controller with Accept: text/occi."""
