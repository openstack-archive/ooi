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


class TestStorageLinkController(test_middleware.TestMiddleware):
    """Test OCCI storage link controller."""
    def test_list_vols_empty(self):
        tenant = fakes.tenants["bar"]
        app = self.get_app()

        for url in ("/storagelink/", "/storagelink"):
            req = self._build_req(url, tenant["id"], method="GET")

            req.environ["HTTP_X_PROJECT_ID"] = tenant["id"]

            resp = req.get_response(app)

            expected_result = ""
            self.assertContentType(resp)
            self.assertExpectedResult(expected_result, resp)
            self.assertEqual(204, resp.status_code)

    def test_list_attachments_empty(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for url in ("/storagelink/", "/storagelink"):
            req = self._build_req(url, tenant["id"], method="GET")

            m = mock.MagicMock()
            m.user.project_id = tenant["id"]
            req.environ["keystone.token_auth"] = m

            resp = req.get_response(app)

            expected_result = ""
            self.assertContentType(resp)
            self.assertExpectedResult(expected_result, resp)
            self.assertEqual(204, resp.status_code)

    def test_list_attachments(self):
        tenant = fakes.tenants["baz"]
        app = self.get_app()

        for url in ("/storagelink/", "/storagelink"):
            req = self._build_req(url, tenant["id"], method="GET")

            resp = req.get_response(app)

            self.assertEqual(200, resp.status_code)
            expected = []
            for v in fakes.volumes[tenant["id"]]:
                for a in v["attachments"]:
                    link_id = '_'.join([a["serverId"], v["id"]])
                    expected.append(
                        ("X-OCCI-Location",
                         utils.join_url(self.application_url + "/",
                                        "storagelink/%s" % link_id))
                    )
            self.assertExpectedResult(expected, resp)

    def test_show_link(self):
        tenant = fakes.tenants["baz"]
        app = self.get_app()

        for volume in fakes.volumes[tenant["id"]]:
            for a in volume["attachments"]:
                link_id = '_'.join([a["serverId"], volume["id"]])
                req = self._build_req("/storagelink/%s" % link_id,
                                      tenant["id"], method="GET")

                resp = req.get_response(app)
                self.assertContentType(resp)
                link_id = '_'.join([a["serverId"], a["volumeId"]])
                source = utils.join_url(self.application_url + "/",
                                        "compute/%s" % a["serverId"])
                target = utils.join_url(self.application_url + "/",
                                        "storage/%s" % a["volumeId"])
                self.assertResultIncludesLinkAttr(link_id, source, target,
                                                  resp)
                self.assertEqual(200, resp.status_code)

    def test_show_invalid_id(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/storagelink/%s" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_show_non_existant_compute(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/storagelink/%s_foo" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_show_non_existant_volume(self):
        tenant = fakes.tenants["foo"]
        server_id = fakes.servers[tenant["id"]][0]["id"]

        app = self.get_app()
        req = self._build_req("/storagelink/%s_foo" % server_id,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_create_link(self):
        tenant = fakes.tenants["foo"]

        server_id = fakes.servers[tenant["id"]][0]["id"]
        server_url = utils.join_url(self.application_url + "/",
                                    "compute/%s" % server_id)
        vol_id = fakes.volumes[tenant["id"]][0]["id"]
        vol_url = utils.join_url(self.application_url + "/",
                                 "storage/%s" % vol_id)

        app = self.get_app()
        headers = {
            'Category': (
                'storagelink;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.core.source="%s", '
                'occi.core.target="%s"'
                ) % (server_url, vol_url)
        }
        req = self._build_req("/storagelink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)

        link_id = '_'.join([server_id, vol_id])
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "storagelink/%s" % link_id))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertDefaults(resp)

    def test_create_link_with_device(self):
        tenant = fakes.tenants["foo"]

        server_id = fakes.servers[tenant["id"]][0]["id"]
        server_url = utils.join_url(self.application_url + "/",
                                    "compute/%s" % server_id)
        vol_id = fakes.volumes[tenant["id"]][0]["id"]
        vol_url = utils.join_url(self.application_url + "/",
                                 "storage/%s" % vol_id)

        app = self.get_app()
        headers = {
            'Category': (
                'storagelink;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.storagelink.deviceid="/dev/vdc", '
                'occi.core.source="%s", '
                'occi.core.target="%s"'
                ) % (server_url, vol_url)
        }
        req = self._build_req("/storagelink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)

        link_id = '_'.join([server_id, vol_id])
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "storagelink/%s" % link_id))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertDefaults(resp)

    def test_delete_link(self):
        tenant = fakes.tenants["baz"]
        app = self.get_app()

        for volume in fakes.volumes[tenant["id"]]:
            for a in volume["attachments"]:
                link_id = '_'.join([a["serverId"], volume["id"]])
                req = self._build_req("/storagelink/%s" % link_id,
                                      tenant["id"], method="DELETE")
                resp = req.get_response(app)
                self.assertContentType(resp)
                self.assertEqual(204, resp.status_code)


class StorageLinkControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                     TestStorageLinkController):
    """Test OCCI storage link controller with Accept: text/plain."""


class StorageLinkControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                    TestStorageLinkController):
    """Test OCCI storage link controller with Accept: text/occi."""
