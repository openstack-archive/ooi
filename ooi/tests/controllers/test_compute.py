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

from ooi.api import compute
from ooi.api import helpers
from ooi.tests.controllers import base
from ooi.tests import fakes


class TestComputeController(base.TestController):
    def setUp(self):
        super(TestComputeController, self).setUp()
        self.controller = compute.Controller(mock.MagicMock(), None)

    def _build_req(self, tenant_id, **kwargs):
        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}

        kwargs["base_url"] = self.application_url

        return webob.Request.blank("/whatever", environ=environ, **kwargs)

    @mock.patch.object(helpers.OpenStackHelper, "index")
    def test_index(self, m_index):
        test_servers = [
            [],
            fakes.servers[fakes.tenants["foo"]["id"]]
        ]

        for servers in test_servers:
            m_index.return_value = servers
            result = self.controller.index(None)
            expected = self.controller._get_compute_resources(servers)
            self.assertEqual(expected, result.resources)
            m_index.assert_called_with(None)

    @mock.patch.object(compute.Controller, "_delete")
    def test_delete(self, mock_delete):
        mock_delete.return_value = []
        ret = self.controller.delete(None, "foo")
        self.assertEqual([], ret)
        mock_delete.assert_called_with(None, ["foo"])

    @mock.patch.object(helpers.OpenStackHelper, "delete")
    def test_delete_ids(self, mock_delete):
        server_ids = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_delete.return_value = None
        ret = self.controller._delete(None, server_ids)
        self.assertEqual([], ret)
        mock_delete.assert_has_calls([mock.call(None, s) for s in server_ids])

    @mock.patch.object(helpers.OpenStackHelper, "index")
    @mock.patch.object(compute.Controller, "_delete")
    def test_delete_all(self, mock_delete, mock_index):
        servers = [{"id": uuid.uuid4().hex}, {"id": uuid.uuid4().hex}]
        mock_index.return_value = servers
        mock_delete.return_value = []
        ret = self.controller.delete_all(None)
        self.assertEqual([], ret)
        mock_delete.assert_called_with(None, [s["id"] for s in servers])
