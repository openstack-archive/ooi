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

from ooi.tests import fakes
from ooi.tests.middleware import test_middleware
from ooi import utils


def build_occi_network(pool_name):
    cats = []
    cats.append('network; '
                'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
                'class="kind"; title="network resource"; '
                'rel="http://schemas.ogf.org/occi/core#resource"; '
                'location="%s/network/"' % fakes.application_url)
    cats.append('ipnetwork; '
                'scheme="http://schemas.ogf.org/occi/infrastructure/'
                'network#"; class="mixin"; title="IP Networking Mixin"')
    attrs = [
        'occi.core.title="%s"' % pool_name,
        'occi.network.state="active"',
        'occi.core.id="%s"' % pool_name,
    ]
    links = []
    links.append('<%s/network/%s?action=up>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#up"' %
                 (fakes.application_url, pool_name))
    links.append('<%s/network/%s?action=down>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#down"' %
                 (fakes.application_url, pool_name))
    result = []
    for c in cats:
        result.append(("Category", c))
    for l in links:
        result.append(("Link", l))
    for a in attrs:
        result.append(("X-OCCI-Attribute", a))
    return result


class TestNetworkController(test_middleware.TestMiddleware):
    """Test OCCI network controller."""

    def test_list_pools_empty(self):
        tenant = fakes.tenants["bar"]
        app = self.get_app()

        for url in ("/network", "/network/"):
            req = self._build_req(url, tenant["id"], method="GET")

            m = mock.MagicMock()
            m.user.project_id = tenant["id"]
            req.environ["keystone.token_auth"] = m

            resp = req.get_response(app)

            expected = [
                ("X-OCCI-Location",
                 utils.join_url(self.application_url + "/", "network/fixed"))
            ]
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)
            self.assertEqual(200, resp.status_code)

    def test_list_pools(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for url in ("/network", "/network/"):
            req = self._build_req(url, tenant["id"], method="GET")

            resp = req.get_response(app)

            self.assertEqual(200, resp.status_code)
            expected = [
                ("X-OCCI-Location",
                 utils.join_url(self.application_url + "/", "network/fixed"))
            ]
            if fakes.pools[tenant["id"]]:
                expected.append(
                    ("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "network/floating"))
                )
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)

    def test_show_floating_pool(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for pool in fakes.pools[tenant["id"]]:
            req = self._build_req("/network/floating", tenant["id"],
                                  method="GET")
            resp = req.get_response(app)
            expected = build_occi_network("floating")
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)
            self.assertEqual(200, resp.status_code)

    def test_show_fixed(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        req = self._build_req("/network/fixed", tenant["id"], method="GET")

        resp = req.get_response(app)
        expected = build_occi_network("fixed")
        self.assertDefaults(resp)
        self.assertExpectedResult(expected, resp)
        self.assertEqual(200, resp.status_code)

    def test_pool_not_found(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/network/%s" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)


class NetworkControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                 TestNetworkController):
    """Test OCCI network controller with Accept: text/plain."""


class NetworkControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                TestNetworkController):
    """Test OCCI network controller with Accept: text/occi."""
