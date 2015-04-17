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

import copy
import uuid

import mock

from ooi.tests import fakes
from ooi.tests.middleware import test_middleware
from ooi import utils


class TestNetInterfaceController(test_middleware.TestMiddleware):
    """Test OCCI network interface controller."""
    def test_list_ifaces_empty(self):
        tenant = fakes.tenants["bar"]
        app = self.get_app()

        for url in ("/networklink/", "/networklink"):
            req = self._build_req(url, tenant["id"], method="GET")

            m = mock.MagicMock()
            m.user.project_id = tenant["id"]
            req.environ["keystone.token_auth"] = m

            resp = req.get_response(app)

            expected_result = ""
            self.assertContentType(resp)
            self.assertExpectedResult(expected_result, resp)
            self.assertEqual(204, resp.status_code)

    def test_list_ifaces(self):
        tenant = fakes.tenants["baz"]
        app = self.get_app()

        for url in ("/networklink/", "/networklink"):
            req = self._build_req(url, tenant["id"], method="GET")

            resp = req.get_response(app)

            self.assertEqual(200, resp.status_code)
            expected = []
            for ip in fakes.floating_ips[tenant["id"]]:
                if ip["instance_id"] is not None:
                    link_id = '_'.join([ip["instance_id"], ip["ip"]])
                    expected.append(
                        ("X-OCCI-Location",
                         utils.join_url(self.application_url + "/",
                                        "networklink/%s" % link_id))
                    )
            self.assertExpectedResult(expected, resp)

    def test_show_iface(self):
        tenant = fakes.tenants["baz"]
        app = self.get_app()

        for ip in fakes.floating_ips[tenant["id"]]:
            if ip["instance_id"] is not None:
                link_id = '_'.join([ip["instance_id"], ip["ip"]])
                req = self._build_req("/networklink/%s" % link_id,
                                      tenant["id"], method="GET")

                resp = req.get_response(app)
                self.assertContentType(resp)
                source = utils.join_url(self.application_url + "/",
                                        "compute/%s" % ip["instance_id"])
                target = utils.join_url(self.application_url + "/",
                                        "network/floating/%s" % ip["pool"])
                self.assertResultIncludesLink(link_id, source, target, resp)
                self.assertEqual(200, resp.status_code)

    def test_show_invalid_id(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/networklink/%s" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_show_non_existant_compute(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/networklink/%s_foo" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_show_non_existant_volume(self):
        tenant = fakes.tenants["foo"]
        server_id = fakes.servers[tenant["id"]][0]["id"]

        app = self.get_app()
        req = self._build_req("/networklink/%s_foo" % server_id,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_create_link_with_fixed(self):
        tenant = fakes.tenants["foo"]
        server_id = fakes.servers[tenant["id"]][0]["id"]
        net_id = "fixed"

        app = self.get_app()
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.core.source="%s", '
                'occi.core.target="%s"'
                ) % (server_id, net_id)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)

        self.assertEqual(400, resp.status_code)

    def test_create_link_with_invalid_net(self):
        tenant = fakes.tenants["foo"]
        server_id = fakes.servers[tenant["id"]][0]["id"]
        net_id = "notexistant"

        app = self.get_app()
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.core.source="%s", '
                'occi.core.target="%s"'
                ) % (server_id, net_id)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_create_link_with_unexistant_net(self):
        tenant = fakes.tenants["foo"]
        server_id = fakes.servers[tenant["id"]][0]["id"]
        net_id = "floating/nothere"

        app = self.get_app()
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.core.source="%s", '
                'occi.core.target="%s"'
                ) % (server_id, net_id)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_create_link(self):
        tenant = fakes.tenants["foo"]

        server_id = fakes.servers[tenant["id"]][0]["id"]
        net_id = "floating/" + fakes.pools[tenant["id"]][0]["id"]

        app = self.get_app()
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.core.source="%s", '
                'occi.core.target="%s"'
                ) % (server_id, net_id)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)

        link_id = '_'.join([server_id, fakes.allocated_ip])
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "networklink/%s" % link_id))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertDefaults(resp)

    def test_delete_fixed(self):
        tenant = fakes.tenants["baz"]
        app = self.get_app()

        for s in fakes.servers[tenant["id"]]:
            addresses = copy.copy(s.get("addresses", {}))
            while addresses:
                addr_set = addresses.popitem()
                for addr in addr_set[1]:
                    if addr["OS-EXT-IPS:type"] == "fixed":
                        link_id = '_'.join([s["id"], addr["addr"]])
                        req = self._build_req("/networklink/%s" % link_id,
                                              tenant["id"], method="DELETE")
                        resp = req.get_response(app)
                        self.assertContentType(resp)
                        self.assertEqual(400, resp.status_code)

    def test_delete_link(self):
        tenant = fakes.tenants["baz"]
        app = self.get_app()

        for s in fakes.servers[tenant["id"]]:
            addresses = copy.copy(s.get("addresses", {}))
            while addresses:
                addr_set = addresses.popitem()
                for addr in addr_set[1]:
                    if addr["OS-EXT-IPS:type"] == "floating":
                        link_id = '_'.join([s["id"], addr["addr"]])
                        req = self._build_req("/networklink/%s" % link_id,
                                              tenant["id"], method="DELETE")
                        resp = req.get_response(app)
                        self.assertContentType(resp)
                        self.assertEqual(204, resp.status_code)


class NetInterfaceControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                      TestNetInterfaceController):
    """Test OCCI network link controller with Accept: text/plain."""


class NetInterfaceControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                     TestNetInterfaceController):
    """Test OCCI network link controller with Accept: text/occi."""
