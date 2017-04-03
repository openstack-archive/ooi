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

import uuid

from ooi.tests import fakes
from ooi.tests.functional.middleware import test_middleware
from ooi import utils


class TestNetInterfaceController(test_middleware.TestMiddleware):
    """Test OCCI network interface controller."""

    def setUp(self):
        super(TestNetInterfaceController, self).setUp()
        self.application_url = fakes.application_url
        self.app = self.get_app()

    def test_list_ifaces_empty(self):
        tenant = fakes.tenants["bar"]

        for url in ("/networklink/", "/networklink"):
            req = self._build_req(url, tenant["id"], method="GET")

            req.environ["HTTP_X_PROJECT_ID"] = tenant["id"]

            resp = req.get_response(self.app)

            expected_result = ""
            self.assertContentType(resp)
            self.assertExpectedResult(expected_result, resp)
            self.assertEqual(204, resp.status_code)

    def test_list_ifaces(self):
        tenant = fakes.tenants["baz"]

        for url in ("/networklink/", "/networklink"):
            req = self._build_req(url, tenant["id"], method="GET")

            resp = req.get_response(self.app)

            self.assertEqual(200, resp.status_code)
            servers = fakes.servers[tenant["id"]]
            expected = []
            for server in servers:
                server_addrs = server.get("addresses", {})
                instance_vm = server["id"]
                for addr_set in server_addrs.values():
                    for addr in addr_set:
                        address = addr['addr']
                        link_id = '_'.join([instance_vm,
                                            address])
                        expected.append(
                            ("X-OCCI-Location",
                             utils.join_url(self.application_url + "/",
                                            "networklink/%s" % link_id)))

            self.assertExpectedResult(expected, resp)

    def test_show_iface(self):
        tenant = fakes.tenants["baz"]
        for p in fakes.ports[tenant["id"]]:
            for ip in p["fixed_ips"]:
                instance_vm = p["server_id"]
                link_id = '_'.join([instance_vm,
                                    ip["ip_address"]]
                                   )
                req = self._build_req("/networklink/%s" % link_id,
                                      tenant["id"], method="GET")

                resp = req.get_response(self.app)
                self.assertContentType(resp)
                source = utils.join_url(self.application_url + "/",
                                        "compute/%s" % instance_vm)
                target = utils.join_url(self.application_url + "/",
                                        "network/%s" % p["net_id"])
                self.assertResultIncludesLinkAttr(link_id, source, target,
                                                  resp)
                self.assertEqual(200, resp.status_code)

    def test_show_invalid_id(self):
        tenant = fakes.tenants["foo"]
        link_id = uuid.uuid4().hex
        req = self._build_req("/networklink/%s" % link_id,
                              tenant["id"], method="GET")
        resp = req.get_response(self.app)
        self.assertEqual(404, resp.status_code)

    def test_create_link_invalid(self):
        tenant = fakes.tenants["foo"]
        net_id = fakes.ports[tenant['id']][0]['net_id']
        occi_net_id = utils.join_url(self.application_url + "/",
                                     "network/%s" % net_id)
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': ('occi.core.source="foo", '
                                 'occi.core.target="%s"'
                                 ) % occi_net_id
        }
        req = self._build_req("/networklink", None, method="POST",
                              headers=headers)
        resp = req.get_response(self.app)
        self.assertEqual(400, resp.status_code)

    def test_create_link_no_pool(self):
        tenant = fakes.tenants["foo"]
        net_id = fakes.ports[tenant['id']][0]['net_id']
        occi_compute_id = utils.join_url(
            self.application_url + "/",
            "compute/%s" % fakes.linked_vm_id)
        occi_net_id = utils.join_url(self.application_url + "/",
                                     "network/%s" % net_id)
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': ('occi.core.source="%s", '
                                 'occi.core.target="%s"'
                                 ) % (occi_compute_id, occi_net_id)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(self.app)
        self.assertEqual(200, resp.status_code)

    def test_create_link_with_pool(self):
        tenant = fakes.tenants["baz"]
        link_info = fakes.ports[tenant['id']][0]

        server_url = utils.join_url(self.application_url + "/",
                                    "compute/%s" % link_info['server_id'])
        net_url = utils.join_url(self.application_url + "/",
                                 "network/%s" % link_info['net_id'])
        pool_name = 'pool'
        headers = {
            'Category': ('networkinterface;'
                         'scheme="http://schemas.ogf.org/occi/'
                         'infrastructure#";'
                         'class="kind",'
                         '%s;'
                         'scheme="http://schemas.openstack.org/network/'
                         'floatingippool#"; class="mixin"') % pool_name,
            'X-OCCI-Attribute': ('occi.core.source="%s", '
                                 'occi.core.target="%s"'
                                 ) % (server_url, net_url)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(self.app)

        link_id = '_'.join([link_info['server_id'],
                            link_info['fixed_ips'][0]
                            ["ip_address"]])
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "networklink/%s" % link_id))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertDefaults(resp)

    def test_create_link_ipreservation(self):
        tenant = fakes.tenants["baz"]
        net_id = fakes.floating_ips[tenant['id']][0]['id']
        occi_compute_id = utils.join_url(
            self.application_url + "/",
            "compute/%s" % fakes.linked_vm_id)
        occi_net_id = utils.join_url(self.application_url + "/",
                                     "ipreservation/%s" % net_id)
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': ('occi.core.source="%s", '
                                 'occi.core.target="%s"'
                                 ) % (occi_compute_id, occi_net_id)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(self.app)
        self.assertEqual(200, resp.status_code)

    def test_delete_fixed(self):
        tenant = fakes.tenants["baz"]

        for n in fakes.ports[tenant["id"]]:
            if n["net_id"] != "PUBLIC":
                if n["server_id"]:
                    link_id = '_'.join([n["server_id"],
                                        n["fixed_ips"]
                                        [0]["ip_address"]])
                    req = self._build_req(
                        "/networklink/%s" % link_id,
                        tenant["id"], method="DELETE")
                    resp = req.get_response(self.app)
                    self.assertContentType(resp)
                    self.assertEqual(204, resp.status_code)

    def test_delete_public(self):
        tenant = fakes.tenants["baz"]
        for n in fakes.floating_ips[tenant["id"]]:
            if n["instance_id"]:
                link_id = '_'.join([n["instance_id"],
                                    n["ip"]])
                req = self._build_req("/networklink/%s" % link_id,
                                      tenant["id"], method="DELETE")
                resp = req.get_response(self.app)
                self.assertContentType(resp)
                self.assertEqual(204, resp.status_code)

    def test_delete_ipreservation(self):
        tenant = fakes.tenants["baz"]
        for n in fakes.floating_ips[tenant["id"]]:
            if n["instance_id"]:
                link_id = '_'.join([n["instance_id"],
                                    n["ip"]])
                req = self._build_req("/networklink/%s" % link_id,
                                      tenant["id"], method="DELETE")
                resp = req.get_response(self.app)
                self.assertContentType(resp)
                self.assertEqual(204, resp.status_code)

    def test_show_non_existant_compute(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/networklink/%s_foo" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_create_link_invalid_compute(self):
        app = self.get_app()
        net_id = utils.join_url(self.application_url + "/",
                                "network/floating")
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': ('occi.core.source="foo", '
                                 'occi.core.target="%s"'
                                 ) % net_id
        }
        req = self._build_req("/networklink", None, method="POST",
                              headers=headers)
        resp = req.get_response(app)
        self.assertEqual(400, resp.status_code)

    def test_create_link_invalid_network(self):
        app = self.get_app()
        server_id = utils.join_url(self.application_url + "/",
                                   "compute/foo")
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': ('occi.core.source="%s", '
                                 'occi.core.target="bar"'
                                 ) % server_id
        }
        req = self._build_req("/networklink", None, method="POST",
                              headers=headers)
        resp = req.get_response(app)
        self.assertEqual(400, resp.status_code)


class NetInterfaceControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                      TestNetInterfaceController):
    """Test OCCI network link controller with Accept: text/plain."""


class NetInterfaceControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                     TestNetInterfaceController):
    """Test OCCI network link controller with Accept: text/occi."""
