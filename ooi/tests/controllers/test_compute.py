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


import mock
import webob

from ooi.api import compute
from ooi.tests import base
from ooi.tests import fakes


class TestController(base.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestController, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestController, self).setUp()
        self.application_url = fakes.application_url

    def assertExpectedReq(self, method, path, body, request):
        self.assertEqual(method, request.method)
        self.assertEqual(path, request.path_info)
        self.assertEqual(body, request.text)


class TestComputeController(TestController):
    def setUp(self):
        super(TestComputeController, self).setUp()
        self.controller = compute.Controller(mock.MagicMock(), None)

    def _build_req(self, tenant_id, **kwargs):
        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}

        kwargs["base_url"] = self.application_url

        return webob.Request.blank("/whatever", environ=environ, **kwargs)

    @mock.patch("webob.Request.get_response")
    def test_index(self, m_get_response):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])

        test_servers = [
            [],
            fakes.servers[fakes.tenants["foo"]["id"]]
        ]

        for servers in test_servers:
            resp_data = {"servers": servers}
            response = fakes.create_fake_json_resp(data=resp_data, status=200)
            m_get_response.return_value = response
            result = self.controller.index(req)
            expected = self.controller._get_compute_resources(servers)
            self.assertItemsEqual(expected, result.resources)

    def test_os_index_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.controller._get_os_index_req(req)
        path = "/%s/servers" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)
