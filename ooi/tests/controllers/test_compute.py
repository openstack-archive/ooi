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

import json
import uuid

import mock
import six
import webob

from ooi.api import compute
from ooi import exception
from ooi.tests.controllers import base
from ooi.tests import fakes


class FakeException(Exception):
    pass


class TestComputeController(base.TestController):
    def setUp(self):
        super(TestComputeController, self).setUp()
        self.controller = compute.Controller(mock.MagicMock(), None)

    def _build_req(self, tenant_id, path="/whatever", **kwargs):
        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}

        kwargs["base_url"] = self.application_url

        return webob.Request.blank(path, environ=environ, **kwargs)

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

    def test_os_delete_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.controller._get_os_delete_req(req, server_uuid)
        path = "/%s/servers/%s" % (tenant["id"], server_uuid)

        self.assertExpectedReq("DELETE", path, "", os_req)

    def test_delete_ids(self):
        tenant = fakes.tenants["foo"]
        server_uuids = [uuid.uuid4().hex, uuid.uuid4().hex]
        req = self._build_req(tenant["id"])
        response = fakes.create_fake_json_resp({}, 204)
        with mock.patch("webob.Request.get_response") as m_get_response:
            m_get_response.return_value = response
            self.controller._delete(req, server_uuids)

    @mock.patch("ooi.api.base.exception_from_response")
    @mock.patch("webob.Request.get_response")
    def test_delete_ids_with_failure(self, m_get_response, m_exc):
        tenant = fakes.tenants["foo"]
        server_uuids = [uuid.uuid4().hex, uuid.uuid4().hex]
        req = self._build_req(tenant["id"])
        response = fakes.create_fake_json_resp({}, 500)

        m_get_response.return_value = response
        m_exc.return_value = FakeException()
        self.assertRaises(FakeException,
                          self.controller._delete,
                          req,
                          server_uuids)

    @mock.patch.object(compute.Controller, "_delete")
    def test_delete(self, m_delete):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        server_uuid = uuid.uuid4().hex
        m_delete.return_value = []
        ret = self.controller.delete(req, server_uuid)
        m_delete.assert_called_with(req, [server_uuid])
        self.assertEqual([], ret)

    @mock.patch.object(compute.Controller, "_get_compute_ids")
    @mock.patch.object(compute.Controller, "_delete")
    def test_delete_all(self, m_delete, m_get_compute_ids):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        server_uuids = [uuid.uuid4().hex, uuid.uuid4().hex]
        m_get_compute_ids.return_value = server_uuids
        m_delete.return_value = []
        ret = self.controller.delete_all(req)
        m_delete.assert_called_with(req, server_uuids)
        self.assertEqual([], ret)

    def test_os_action_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        server_uuid = uuid.uuid4().hex

        actions_map = {
            "stop": json.dumps({"os-stop": None}),
            "start": json.dumps({"os-start": None}),
            "restart": json.dumps({"reboot": {"type": "SOFT"}}),
        }

        path = "/%s/servers/%s/action" % (tenant["id"], server_uuid)

        for act, body in six.iteritems(actions_map):
            os_req = self.controller._get_os_run_action(req, act, server_uuid)
            self.assertExpectedReq("POST", path, body, os_req)

    def test_run_action_none(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        self.assertRaises(exception.InvalidAction,
                          self.controller.run_action,
                          req,
                          None,
                          None)

    def test_run_action_invalid(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"], path="/foo?action=foo")
        server_uuid = uuid.uuid4().hex
        self.assertRaises(exception.InvalidAction,
                          self.controller.run_action,
                          req,
                          server_uuid,
                          None)

    def test_run_action_not_implemented(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"], path="/foo?action=suspend")
        req.get_parser = mock.MagicMock()
        server_uuid = uuid.uuid4().hex
        self.assertRaises(exception.NotImplemented,
                          self.controller.run_action,
                          req,
                          server_uuid,
                          None)

    @mock.patch("webob.Request.get_response")
    @mock.patch("ooi.occi.validator.Validator")
    def test_run_action_start(self, m_validator, m_get_response):
        tenant = fakes.tenants["foo"]
        for action in ("stop", "start", "restart"):
            req = self._build_req(tenant["id"], path="/foo?action=%s" % action)
            req.get_parser = mock.MagicMock()
            server_uuid = uuid.uuid4().hex
            m_get_response.return_value = fakes.create_fake_json_resp({}, 202)
            ret = self.controller.run_action(req, server_uuid, None)
            m_get_response.assert_called()
            self.assertEqual([], ret)

    @mock.patch("ooi.api.base.exception_from_response")
    @mock.patch("webob.Request.get_response")
    @mock.patch("ooi.occi.validator.Validator")
    def test_run_action_with_failure(self, m_validator, m_get_response, m_exc):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"], path="/foo?action=start")
        req.get_parser = mock.MagicMock()
        server_uuid = uuid.uuid4().hex
        m_get_response.return_value = fakes.create_fake_json_resp({}, 500)
        m_exc.return_value = FakeException()
        self.assertRaises(FakeException,
                          self.controller.run_action,
                          req,
                          server_uuid,
                          None)
