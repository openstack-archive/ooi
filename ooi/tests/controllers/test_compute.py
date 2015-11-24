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
import webob.exc

from ooi.api import compute
from ooi.api import helpers
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute as occi_compute
from ooi.openstack import contextualization
from ooi.openstack import templates
from ooi.tests import base
from ooi.tests import fakes


class TestComputeController(base.TestController):
    def setUp(self):
        super(TestComputeController, self).setUp()
        self.controller = compute.Controller(mock.MagicMock(), None)

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

    @mock.patch.object(helpers.OpenStackHelper, "run_action")
    @mock.patch.object(helpers.OpenStackHelper, "get_server")
    @mock.patch("ooi.occi.validator.Validator")
    def test_run_action_start(self, m_validator, m_get_server, m_run_action):
        tenant = fakes.tenants["foo"]
#        for action in ("stop", "start", "restart", "suspend"):
        action = "start"

        state_action_map = {
            "SUSPENDED": "resume",
            "PAUSED": "unpause",
            "STOPPED": "start",
        }

        req = self._build_req(tenant["id"], path="/foo?action=start")
        for state, action in six.iteritems(state_action_map):
            req.get_parser = mock.MagicMock()
            server_uuid = uuid.uuid4().hex
            server = {"status": state}
            m_get_server.return_value = server
            m_run_action.return_value = None
            ret = self.controller.run_action(req, server_uuid, None)
            self.assertEqual([], ret)
            m_run_action.assert_called_with(mock.ANY, action, server_uuid)

    @mock.patch.object(helpers.OpenStackHelper, "get_server_volumes_link")
    @mock.patch.object(helpers.OpenStackHelper, "get_image")
    @mock.patch.object(helpers.OpenStackHelper, "get_flavor")
    @mock.patch.object(helpers.OpenStackHelper, "get_server")
    def test_show(self, m_server, m_flavor, m_image, m_vol):
        for tenant in fakes.tenants.values():
            servers = fakes.servers[tenant["id"]]
            for server in servers:
                flavor = fakes.flavors[server["flavor"]["id"]]
                image = fakes.images[server["image"]["id"]]
                volumes = fakes.volumes.get(tenant["id"], [])
                if volumes:
                    volumes = volumes[0]["attachments"]

                m_server.return_value = server
                m_flavor.return_value = flavor
                m_image.return_value = image
                m_vol.return_value = volumes

                ret = self.controller.show(None, server["id"])
                # FIXME(aloga): Should we test the resource?
                self.assertIsInstance(ret[0], occi_compute.ComputeResource)
                m_server.assert_called_with(None, server["id"])
                m_flavor.assert_called_with(None, flavor["id"])
                m_image.assert_called_with(None, image["id"])
                m_vol.assert_called_with(None, server["id"])

    @mock.patch.object(helpers.OpenStackHelper, "get_server_volumes_link")
    @mock.patch.object(helpers.OpenStackHelper, "get_image")
    @mock.patch.object(helpers.OpenStackHelper, "get_flavor")
    @mock.patch.object(helpers.OpenStackHelper, "get_server")
    def test_show_no_image(self, m_server, m_flavor, m_image, m_vol):
        for tenant in fakes.tenants.values():
            servers = fakes.servers[tenant["id"]]
            for server in servers:
                flavor = fakes.flavors[server["flavor"]["id"]]
                image = fakes.images[server["image"]["id"]]
                volumes = fakes.volumes.get(tenant["id"], [])
                if volumes:
                    volumes = volumes[0]["attachments"]

                m_server.return_value = server
                m_flavor.return_value = flavor
                m_image.side_effect = webob.exc.HTTPNotFound()
                m_vol.return_value = volumes

                ret = self.controller.show(None, server["id"])
                # FIXME(aloga): Should we test the resource?
                self.assertIsInstance(ret[0], occi_compute.ComputeResource)
                m_server.assert_called_with(None, server["id"])
                m_flavor.assert_called_with(None, flavor["id"])
                m_image.assert_called_with(None, image["id"])
                m_vol.assert_called_with(None, server["id"])

    @mock.patch.object(helpers.OpenStackHelper, "create_server")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_server(self, m_validator, m_create):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        obj = {
            "attributes": {
                "occi.core.title": "foo instance",
            },
            "schemes": {
                templates.OpenStackOSTemplate.scheme: ["foo"],
                templates.OpenStackResourceTemplate.scheme: ["bar"],
            },
        }
        # NOTE(aloga): the mocked call is
        # "parser = req.get_parser()(req.headers, req.body)"
        req.get_parser = mock.MagicMock()
        # NOTE(aloga): MOG!
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        server = {"id": uuid.uuid4().hex}
        m_create.return_value = server
        ret = self.controller.create(req, None)
        self.assertIsInstance(ret, collection.Collection)
        m_create.assert_called_with(mock.ANY, "foo instance", "foo", "bar",
                                    user_data=None,
                                    key_name=None)

    @mock.patch.object(helpers.OpenStackHelper, "create_server")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_server_with_context(self, m_validator, m_create):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        obj = {
            "attributes": {
                "occi.core.title": "foo instance",
                "org.openstack.compute.user_data": "bazonk",
            },
            "schemes": {
                templates.OpenStackOSTemplate.scheme: ["foo"],
                templates.OpenStackResourceTemplate.scheme: ["bar"],
                contextualization.user_data.scheme: None,
                contextualization.public_key.scheme: None,
            },
        }
        # NOTE(aloga): the mocked call is
        # "parser = req.get_parser()(req.headers, req.body)"
        req.get_parser = mock.MagicMock()
        # NOTE(aloga): MOG!
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        server = {"id": uuid.uuid4().hex}
        m_create.return_value = server
        ret = self.controller.create(req, None)  # noqa
        self.assertIsInstance(ret, collection.Collection)
        m_create.assert_called_with(mock.ANY, "foo instance", "foo", "bar",
                                    user_data="bazonk",
                                    key_name=None)

    @mock.patch.object(helpers.OpenStackHelper, "keypair_create")
    @mock.patch.object(helpers.OpenStackHelper, "create_server")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_server_with_sshkeys(self, m_validator, m_server,
                                        m_keypair):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        obj = {
            "attributes": {
                "occi.core.title": "foo instance",
                "org.openstack.credentials.publickey.name": "wtfoo",
                "org.openstack.credentials.publickey.data": "wtfoodata"
            },
            "schemes": {
                templates.OpenStackOSTemplate.scheme: ["foo"],
                templates.OpenStackResourceTemplate.scheme: ["bar"],
                contextualization.public_key.scheme: None,
            },
        }
        req.get_parser = mock.MagicMock()
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        server = {"id": uuid.uuid4().hex}
        m_server.return_value = server
        m_keypair.return_value = None
        ret = self.controller.create(req, None)  # noqa
        self.assertIsInstance(ret, collection.Collection)
        m_keypair.assert_called_with(mock.ANY, "wtfoo",
                                     public_key="wtfoodata")
        m_server.assert_called_with(mock.ANY, "foo instance", "foo", "bar",
                                    user_data=None,
                                    key_name="wtfoo")

    @mock.patch.object(helpers.OpenStackHelper, "keypair_delete")
    @mock.patch.object(helpers.OpenStackHelper, "keypair_create")
    @mock.patch.object(helpers.OpenStackHelper, "create_server")
    @mock.patch("ooi.occi.validator.Validator")
    def test_create_server_with_no_sshkey_name(self, m_validator, m_server,
                                               m_keypair, m_keypair_delete):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        obj = {
            "attributes": {
                "occi.core.title": "foo instance",
                "org.openstack.credentials.publickey.data": "wtfoodata"
            },
            "schemes": {
                templates.OpenStackOSTemplate.scheme: ["foo"],
                templates.OpenStackResourceTemplate.scheme: ["bar"],
                contextualization.public_key.scheme: None,
            },
        }
        req.get_parser = mock.MagicMock()
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        server = {"id": uuid.uuid4().hex}
        m_server.return_value = server
        m_keypair.return_value = None
        ret = self.controller.create(req, None)  # noqa
        self.assertIsInstance(ret, collection.Collection)
        m_keypair.assert_called_with(mock.ANY, mock.ANY,
                                     public_key="wtfoodata")
        m_server.assert_called_with(mock.ANY, "foo instance", "foo", "bar",
                                    user_data=None,
                                    key_name=mock.ANY)
        m_keypair_delete.assert_called_with(mock.ANY, mock.ANY)
