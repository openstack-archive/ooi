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

from ooi.api import helpers
from ooi.api import storage as storage_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import storage
from ooi.tests import base
from ooi.tests import fakes


class TestStorageController(base.TestController):
    def setUp(self):
        super(TestStorageController, self).setUp()
        self.controller = storage_api.Controller(mock.MagicMock(), None)

    def _build_req(self, tenant_id, path="/whatever", **kwargs):
        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}

        kwargs["base_url"] = self.application_url

        return webob.Request.blank(path, environ=environ, **kwargs)

    @mock.patch.object(helpers.OpenStackHelper, "get_volumes")
    def test_index(self, m_volumes):
        for tenant in fakes.tenants.values():
            vols = fakes.volumes[tenant["id"]]
            m_volumes.return_value = vols
            ret = self.controller.index(None)
            self.assertIsInstance(ret, collection.Collection)
            for idx, vol in enumerate(vols):
                self.assertIsInstance(ret.resources[idx],
                                      storage.StorageResource)
                self.assertEqual(vol["id"], ret.resources[idx].id)
                m_volumes.assert_called_with(None)

    @mock.patch.object(storage_api.Controller, "_delete")
    def test_delete(self, mock_delete):
        mock_delete.return_value = []
        ret = self.controller.delete(None, "foo")
        self.assertEqual([], ret)
        mock_delete.assert_called_with(None, ["foo"])

    @mock.patch.object(helpers.OpenStackHelper, "volume_delete")
    def test_delete_ids(self, mock_delete):
        vol_ids = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_delete.return_value = None
        ret = self.controller._delete(None, vol_ids)
        self.assertEqual([], ret)
        mock_delete.assert_has_calls([mock.call(None, s) for s in vol_ids])

    @mock.patch.object(helpers.OpenStackHelper, "get_volumes")
    @mock.patch.object(storage_api.Controller, "_delete")
    def test_delete_all(self, mock_delete, mock_get_volumes):
        vols = [{"id": uuid.uuid4().hex}, {"id": uuid.uuid4().hex}]
        mock_get_volumes.return_value = vols
        mock_delete.return_value = []
        ret = self.controller.delete_all(None)
        self.assertEqual([], ret)
        mock_delete.assert_called_with(None, [v["id"] for v in vols])

    @mock.patch.object(helpers.OpenStackHelper, "get_volume")
    def test_show(self, m_vol):
        for tenant in fakes.tenants.values():
            vols = fakes.volumes[tenant["id"]]
            for idx, vol in enumerate(vols):
                m_vol.return_value = vol
                ret = self.controller.show(None, vol["id"])[0]
                self.assertIsInstance(ret, storage.StorageResource)
                self.assertEqual(vol["id"], ret.id)
                self.assertEqual(vol["displayName"], ret.title)
                self.assertEqual(vol["size"], ret.size)
                m_vol.assert_called_with(None, vol["id"])

    @mock.patch.object(helpers.OpenStackHelper, "volume_create")
    @mock.patch("ooi.occi.validator.Validator")
    def test_volume_create(self, m_validator, m_create):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo volume"
        size = "10"
        obj = {
            "attributes": {
                "occi.core.title": name,
                "occi.storage.size": size,
            }
        }
        # NOTE(aloga): the mocked call is
        # "parser = req.get_parser()(req.headers, req.body)"
        req.get_parser = mock.MagicMock()
        # NOTE(aloga): MOG!
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        volume = {
            "id": uuid.uuid4().hex,
            "displayName": name,
            "size": size,
            "status": "ACTIVE",
        }
        m_create.return_value = volume
        ret = self.controller.create(req, None)
        self.assertIsInstance(ret, collection.Collection)
        m_create.assert_called_with(mock.ANY, name, size)

    @mock.patch("ooi.occi.validator.Validator")
    def test_volume_create_invalid(self, m_validator):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo volume"
        obj = {
            "attributes": {
                "occi.core.title": name,
            }
        }
        # NOTE(aloga): the mocked call is
        # "parser = req.get_parser()(req.headers, req.body)"
        req.get_parser = mock.MagicMock()
        # NOTE(aloga): MOG!
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        self.assertRaises(exception.Invalid,
                          self.controller.create,
                          req,
                          None)

    def test_actions(self):
        tenant = fakes.tenants["foo"]
        actions = ("online", "offline", "backup", "snapshot", "resize")
        for action in actions:
            req = self._build_req(tenant["id"], path="/foo?action=%s" % action)
            vol_id = uuid.uuid4().hex
            self.assertRaises(exception.NotImplemented,
                              self.controller.run_action,
                              req, vol_id, None)

    def test_invalid_action(self):
        tenant = fakes.tenants["foo"]
        actions = ("foo", "")
        for action in actions:
            req = self._build_req(tenant["id"], path="/foo?action=%s" % action)
            vol_id = uuid.uuid4().hex
            self.assertRaises(exception.InvalidAction,
                              self.controller.run_action,
                              req, vol_id, None)
