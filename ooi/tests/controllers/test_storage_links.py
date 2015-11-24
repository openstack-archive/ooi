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

from ooi.api import helpers
from ooi.api import storage_link as storage_link_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link
from ooi.tests import base
from ooi.tests import fakes


class TestStorageLinkController(base.TestController):
    def setUp(self):
        super(TestStorageLinkController, self).setUp()
        self.controller = storage_link_api.Controller(mock.MagicMock(), None)

    @mock.patch.object(helpers.OpenStackHelper, "get_volumes")
    def test_index(self, m_volumes):
        for tenant in fakes.tenants.values():
            vols = fakes.volumes[tenant["id"]]
            m_volumes.return_value = vols
            ret = self.controller.index(None)
            self.assertIsInstance(ret, collection.Collection)
            # NOTE(aloga): the only tenant with an attachment
            if tenant["name"] == "baz":
                for idx, vol in enumerate(vols):
                    self.assertIsInstance(ret.resources[idx],
                                          storage_link.StorageLink)
                    server_id = vol["attachments"][0]["server_id"]
                    link_id = "%s_%s" % (server_id, vol["id"])
                    self.assertEqual(link_id, ret.resources[idx].id)
            else:
                self.assertEqual([], ret.resources)
            m_volumes.assert_called_with(None)

    @mock.patch.object(helpers.OpenStackHelper, "delete_server_volumes_link")
    @mock.patch.object(storage_link_api.Controller, "_get_attachment_from_id")
    def test_delete(self, mock_get, mock_delete):
        server_id = uuid.uuid4().hex
        vol_id = uuid.uuid4().hex
        link_id = "%s_%s" % (server_id, vol_id)
        mock_get.return_value = {"serverId": server_id, "volumeId": vol_id}
        mock_delete.return_value = []
        ret = self.controller.delete(None, link_id)
        self.assertEqual([], ret)
        mock_delete.assert_called_with(None, server_id, vol_id)
        mock_get.assert_called_with(None, link_id)

    @mock.patch.object(storage_link_api.Controller, "_get_attachment_from_id")
    def test_show(self, m_get):
        server_id = uuid.uuid4().hex
        vol_id = uuid.uuid4().hex
        link_id = "%s_%s" % (server_id, vol_id)
        m_get.return_value = {
            "serverId": server_id,
            "volumeId": vol_id,
            "device": "/dev/sda",
        }
        ret = self.controller.show(None, link_id)
        link = ret.pop()
        self.assertIsInstance(link, storage_link.StorageLink)
        self.assertIsInstance(link.source, compute.ComputeResource)
        self.assertIsInstance(link.target, storage.StorageResource)
        self.assertEqual(vol_id, link.target.id)
        self.assertEqual(server_id, link.source.id)
        m_get.assert_called_with(None, link_id)

    @mock.patch.object(helpers.OpenStackHelper, "get_server_volumes_link")
    def test_get_attachment_from_id(self, m_get):
        server_uuid = uuid.uuid4().hex
        vol_uuid = uuid.uuid4().hex
        link_id = "%s_%s" % (server_uuid, vol_uuid)
        m_get.return_value = [
            {"volumeId": uuid.uuid4().hex},
            {"volumeId": vol_uuid},
        ]
        self.assertEqual({"volumeId": vol_uuid},
                         self.controller._get_attachment_from_id(None,
                                                                 link_id))
        link_id = "%s_%s" % (uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertRaises(exception.LinkNotFound,
                          self.controller._get_attachment_from_id,
                          None,
                          link_id)

    def test_get_attachment_from_id_invalid(self):
        self.assertRaises(exception.LinkNotFound,
                          self.controller._get_attachment_from_id,
                          None,
                          "foobarbaz")

    @mock.patch.object(helpers.OpenStackHelper, "create_server_volumes_link")
    @mock.patch("ooi.occi.validator.Validator")
    @mock.patch("ooi.api.helpers.get_id_with_kind")
    def test_create_link(self, m_get_id, m_validator, m_create):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        vol_id = uuid.uuid4().hex
        server_id = uuid.uuid4().hex
        obj = {
            "attributes": {
                "occi.core.target": vol_id,
                "occi.core.source": server_id,
            }
        }
        # NOTE(aloga): the mocked call is
        # "parser = req.get_parser()(req.headers, req.body)"
        req.get_parser = mock.MagicMock()
        # NOTE(aloga): MOG!
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        m_get_id.side_effect = [('', vol_id), ('', server_id)]
        attachment = {
            "device": "/dev/vdd",
            "id": "a26887c6-c47b-4654-abb5-dfadf7d3f803",
            "serverId": server_id,
            "volumeId": vol_id,
        }
        m_create.return_value = attachment
        ret = self.controller.create(req, None)
        link = ret.resources.pop()
        self.assertIsInstance(link, storage_link.StorageLink)
        self.assertIsInstance(link.source, compute.ComputeResource)
        self.assertIsInstance(link.target, storage.StorageResource)
        self.assertEqual(vol_id, link.target.id)
        self.assertEqual(server_id, link.source.id)
        m_create.assert_called_with(mock.ANY, server_id, vol_id, dev=None)
