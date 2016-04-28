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
import uuid

import mock

from ooi.api import helpers
from ooi import exception
from ooi.tests import base
from ooi.tests import fakes_neutron as fakes


class TestNovaNetOpenStackHelper(base.TestCase):
    def setUp(self):
        super(TestNovaNetOpenStackHelper, self).setUp()
        self.version = "version foo bar baz"
        self.helper = helpers.OpenStackNovaNetwork(None, self.version)
        self.translation = {"networks": {
            "occi.core.title": "label",
            "occi.core.id": "id",
            "occi.network.address": "cidr",
            "occi.network.gateway": "gateway",
        }
        }

    @mock.patch.object(helpers.OpenStackNovaNetwork, "_make_get_request")
    def test_index(self, m):
        id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp({"networks": [{"id": id}]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.index(None, None)
        self.assertEqual(id, ret[0]['id'])
        m.assert_called_with(None, "os-networks", None)

    @mock.patch.object(helpers.OpenStackNovaNetwork, "_make_get_request")
    def test_get_network(self, m):
        id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE", "id": id}}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network_details(None, id)
        self.assertEqual("active", ret["state"])
        m.assert_called_with(None, "os-networks/%s" % id)

    @mock.patch.object(helpers.OpenStackNovaNetwork, "_get_req")
    @mock.patch.object(helpers.BaseHelper, "tenant_from_req")
    def test_get_network2(self, m_t, m_rq):
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
            query_string=None)

    @mock.patch.object(helpers.OpenStackNovaNetwork, "_make_create_request")
    def test_create_net(self, m):
        name = "name_net"
        net_id = uuid.uuid4().hex
        cidr = "0.0.0.0"
        gate_way = "0.0.0.1"
        parameters = {"occi.core.title": name,
                      "occi.core.id": net_id,
                      "occi.network.address": cidr,
                      "occi.network.gateway": gate_way
                      }
        self.assertRaises(exception.NotImplemented,
                          self.helper.create_network,
                          None,
                          parameters)
