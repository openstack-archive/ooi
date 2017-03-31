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

import mock

from ooi.api import helpers
from ooi.api import securitygroup_link as securitygroup_link_api
from ooi.occi.core import collection
from ooi.occi.infrastructure import securitygroup_link
from ooi.openstack import helpers as os_helpers
from ooi.tests import base
from ooi.tests import fakes as fakes_nova


class TestNetworkLinkController(base.TestController):
    def setUp(self):
        super(TestNetworkLinkController, self).setUp()
        self.controller = securitygroup_link_api.Controller(
            mock.MagicMock(), None)

    @mock.patch.object(helpers.OpenStackHelper, "list_server_security_links")
    def test_index(self, mock_list):
        tenant_id = fakes_nova.tenants['bar']["id"]
        servers = fakes_nova.servers[tenant_id]
        sg = fakes_nova.security_groups[tenant_id]
        segroup = os_helpers.build_security_group_from_nova(sg)[0]
        links = []
        for server in servers:
            link = {
                "compute_id": server["id"],
                "securitygroup": segroup
            }
            links.append(link)
        mock_list.return_value = links
        ret = self.controller.index(None)
        self.assertIsInstance(ret, collection.Collection)

    @mock.patch.object(helpers.OpenStackHelper, "get_server_security_link")
    @mock.patch.object(helpers.OpenStackHelper, "list_security_groups")
    def test_show(self, mock_list, mock_get):
        tenant_id = fakes_nova.tenants['baz']["id"]
        server = fakes_nova.servers[tenant_id][0]
        server_id = server['id']
        secgroup_name = server['security_groups'][0]["name"]
        link_id = '%s_%s' % (server_id, secgroup_name)
        sec_group = os_helpers.build_security_group_from_nova(
            fakes_nova.security_groups[tenant_id]
        )
        link = {
            "compute_id": server_id,
            "securitygroup": sec_group[0]
        }

        mock_get.return_value = [link]
        mock_list.return_value = sec_group
        ret = self.controller.show(None, link_id)
        self.assertIsInstance(ret, securitygroup_link.SecurityGroupLink)

    @mock.patch.object(helpers.OpenStackHelper, "delete_server_security_link")
    def test_delete(self, mock_del):
        tenant_id = fakes_nova.tenants['baz']["id"]
        server = fakes_nova.servers[tenant_id][0]
        server_id = server['id']
        secgroup_name = server['security_groups'][0]["name"]
        link_id = '%s_%s' % (server_id, secgroup_name)
        mock_del.return_value = []
        ret = self.controller.delete(None, link_id)
        self.assertEqual([], ret)

    @mock.patch.object(helpers.OpenStackHelper, "create_server_security_link")
    @mock.patch("ooi.occi.validator.Validator")
    @mock.patch("ooi.api.helpers.get_id_with_kind")
    def test_create(self, m_get_id, m_validator, m_create):
        compute_id = uuid.uuid4().hex
        sec_id = uuid.uuid4().hex
        obj = {
            "attributes": {
                "occi.core.target": sec_id,
                "occi.core.source": compute_id
            }
        }
        req = self._build_req(uuid.uuid4().hex)
        req.get_parser = mock.MagicMock()
        req.get_parser.return_value.return_value.parse.return_value = obj
        m_validator.validate.return_value = True
        m_get_id.side_effect = [('', compute_id), ('', sec_id)]
        m_create.return_value = []
        ret = self.controller.create(req, None)
        link = ret.resources.pop()
        self.assertIsInstance(link, securitygroup_link.SecurityGroupLink)