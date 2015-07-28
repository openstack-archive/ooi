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
import six
import webob

from ooi.api import helpers
from ooi.tests.controllers import base
from ooi.tests import fakes


class TestOpenStackHelper(base.TestController):
    def setUp(self):
        super(TestOpenStackHelper, self).setUp()
        self.helper = helpers.OpenStackHelper(mock.MagicMock(), None)

    def _build_req(self, tenant_id, **kwargs):
        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}
        return webob.Request.blank("/whatever", environ=environ, **kwargs)

    def test_os_index_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_index_req(req)
        path = "/%s/servers" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_os_delete_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_delete_req(req, server_uuid)
        path = "/%s/servers/%s" % (tenant["id"], server_uuid)

        self.assertExpectedReq("DELETE", path, "", os_req)

    def test_os_action_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        server_uuid = uuid.uuid4().hex

        actions_map = {
            "stop": {"os-stop": None},
            "start": {"os-start": None},
            "restart": {"reboot": {"type": "SOFT"}},
        }

        path = "/%s/servers/%s/action" % (tenant["id"], server_uuid)

        for act, body in six.iteritems(actions_map):
            os_req = self.helper._get_run_action_req(req, act, server_uuid)
            self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_server_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_server_req(req, server_uuid)
        path = "/%s/servers/%s" % (tenant["id"], server_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_flavors_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_flavors_req(req)
        path = "/%s/flavors/detail" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_flavor_req(self):
        tenant = fakes.tenants["foo"]
        flavor_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_flavor_req(req, flavor_uuid)
        path = "/%s/flavors/%s" % (tenant["id"], flavor_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_images_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_images_req(req)
        path = "/%s/images/detail" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_image_req(self):
        tenant = fakes.tenants["foo"]
        image_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_image_req(req, image_uuid)
        path = "/%s/images/%s" % (tenant["id"], image_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_volumes_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_volumes_req(req, server_uuid)
        path = "/%s/servers/%s/os-volume_attachments" % (tenant["id"],
                                                         server_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_floating_ips(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_floating_ips(req)
        path = "/%s/os-floating-ips" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_get_server_create(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo server"
        image = "bar image"
        flavor = "baz flavor"

        body = {
            "server": {
                "name": name,
                "imageRef": image,
                "flavorRef": flavor,
            }
        }

        path = "/%s/servers" % tenant["id"]
        os_req = self.helper._get_create_server_req(req, name, image, flavor)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_get_server_create_with_user_data(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo server"
        image = "bar image"
        flavor = "baz flavor"
        user_data = "bazonk"

        body = {
            "server": {
                "name": name,
                "imageRef": image,
                "flavorRef": flavor,
                "user_data": user_data,
            },
        }

        path = "/%s/servers" % tenant["id"]
        os_req = self.helper._get_create_server_req(req, name, image, flavor,
                                                    user_data=user_data)
        self.assertExpectedReq("POST", path, body, os_req)
