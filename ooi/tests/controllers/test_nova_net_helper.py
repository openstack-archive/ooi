# -*- coding: utf-8 -*-

# Copyright 2016 LIP - Lisbon
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

from ooi.api import helpers
from ooi.tests import base
from ooi.tests import fakes_network as fakes
from ooi import utils


class TestNovaNetOpenStackHelper(base.TestCase):
    def setUp(self):
        super(TestNovaNetOpenStackHelper, self).setUp()
        self.version = "version foo bar baz"
        self.helper = helpers.OpenStackHelper(None, self.version)
        self.translation = {"networks": {
            "occi.core.title": "label",
            "occi.core.id": "id",
            "occi.network.address": "cidr",
            "occi.network.gateway": "gateway",
        }
        }

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_list_networks_with_public(self, m_t, m_rq):
        id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp({"networks": [{"id": id}]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_rq.return_value = req_mock
        ret = self.helper.list_networks(None, None)
        self.assertEqual(2, ret.__len__())

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_list_networks(self, m_t, m_rq):
        id = uuid.uuid4().hex
        tenant_id = uuid.uuid4().hex
        m_t.return_value = tenant_id
        resp = fakes.create_fake_json_resp({"networks": [{"id": id}]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_rq.return_value = req_mock
        ret = self.helper.list_networks(None, None)
        self.assertEqual(id, ret[0]['id'])
        m_rq.assert_called_with(
            None, method="GET",
            path="/%s/os-networks" % (tenant_id),
        )

    def test_get_network_public(self):
        id = 'PUBLIC'
        ret = self.helper.get_network_details(None, id)
        self.assertEqual(id, ret["id"])

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_get_network(self, m_t, m_rq):
        id = uuid.uuid4().hex
        address = uuid.uuid4().hex
        gateway = uuid.uuid4().hex
        label = "network11"
        tenant_id = uuid.uuid4().hex
        m_t.return_value = tenant_id
        resp = fakes.create_fake_json_resp(
            {"network": {"id": id, "label": label,
                         "cidr": address,
                         "gateway": gateway}}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_rq.return_value = req_mock
        ret = self.helper.get_network_details(None, id)
        self.assertEqual(id, ret["id"])
        self.assertEqual(address, ret["address"])
        self.assertEqual(gateway, ret["gateway"])
        self.assertEqual(label, ret["name"])
        m_rq.assert_called_with(
            None, method="GET",
            path="/%s/os-networks/%s" % (tenant_id, id),
            )

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_create_net(self, m_t, m_rq):
        tenant_id = uuid.uuid4().hex
        m_t.return_value = tenant_id
        name = "name_net"
        net_id = uuid.uuid4().hex
        cidr = "0.0.0.0"
        gateway = "0.0.0.1"
        parameters = {"occi.core.title": name,
                      "occi.network.address": cidr,
                      "occi.network.gateway": gateway
                      }
        resp = fakes.create_fake_json_resp(
            {"network": {"id": net_id, "label": name,
                         "cidr": cidr,
                         "gateway": gateway}}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_rq.return_value = req_mock
        ret = self.helper.create_network(None, parameters)
        net_param = utils.translate_parameters(
            self.translation['networks'], parameters)
        body = utils.make_body('network', net_param)
        m_rq.assert_called_with(
            None, method="POST",
            content_type='application/json',
            path="/%s/os-networks" % (tenant_id),
            body=json.dumps(body)
        )
        self.assertEqual(cidr, ret['address'])
        self.assertEqual(name, ret['name'])
        self.assertEqual(gateway, ret['gateway'])
        self.assertEqual(net_id, ret['id'])

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_delete_net(self, m_t, m_rq):
        tenant_id = uuid.uuid4().hex
        m_t.return_value = tenant_id
        net_id = uuid.uuid4().hex
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = []
        m_rq.return_value = req_mock
        ret = self.helper.delete_network(None, net_id)
        self.assertEqual(ret, [])
        m_rq.assert_called_with(
            None, method="DELETE",
            path="/%s/os-networks/%s" % (tenant_id, net_id),
        )