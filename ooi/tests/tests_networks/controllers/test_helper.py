# -*- coding: utf-8 -*-

# Copyright 2015 LIP - Lisbon
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

import mock

from ooi.api.networks import helpers
from ooi.api.networks import parsers
from ooi.tests import base
from ooi.tests.tests_networks import fakes


class TestNetOpenStackHelper(base.TestCase):
    def setUp(self):
        super(TestNetOpenStackHelper, self).setUp()
        self.version = "version foo bar baz"
        self.helper = helpers.OpenStackNet(self.version)
        self.translation = {"network": {"occi.core.title": "name",
                                        "occi.core.id": "network_id",
                                        "occi.network.state": "status",
                                        "X_PROJECT_ID": "tenant_id",
                                        },
                            "subnet": {"occi.core.id": "network_id",
                                       "occi.network.ip_version": "ip_version",
                                       "occi.networkinterface.address": "cidr",
                                       "occi.networkinterface.gateway":
                                           "gateway_ip"
                                       }
                            }

    @mock.patch.object(helpers.OpenStackNet, "_make_get_request")
    def test_index(self, m):
        resp = fakes.create_fake_json_resp({"networks": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.index(None, None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None, "/networks", None)

    @mock.patch.object(helpers.OpenStackNet, "_get_req")
    def test_index2(self, m):
        resp = fakes.create_fake_json_resp({"networks": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.index(None, None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None, method="GET",
                             path="/networks", query_string=None)

    @mock.patch.object(helpers.OpenStackNet, "_make_get_request")
    def test_get_network(self, m):
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE"}}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network(None, 1)
        self.assertEqual("ACTIVE", ret["status"])
        m.assert_called_with(None, "/networks/%s" % 1)

    @mock.patch.object(helpers.OpenStackNet, "_get_req")
    def test_get_network2(self, m):
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE"}}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network(None, 1)
        self.assertEqual("ACTIVE", ret["status"])
        m.assert_called_with(None, method="GET",
                             path="/networks/1", query_string=None)

    @mock.patch.object(helpers.OpenStackNet, "_make_get_request")
    def test_get_subnetwork(self, m):
        resp = fakes.create_fake_json_resp(
            {"subnet": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_subnet(None, 1)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None, "/subnets/%s" % 1)

    @mock.patch.object(helpers.OpenStackNet, "_make_get_request")
    def test_get_network_with_subnet(self, m):
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE", "subnets": [2]},
             "subnet": ["FOO"]}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network(None, 1)
        self.assertEqual("ACTIVE", ret["status"])
        self.assertEqual([2], ret["subnets"])
        self.assertEqual(["FOO"], ret["subnet_info"])
        m.assert_called_with(req_mock, "/subnets/2")

    @mock.patch.object(helpers.OpenStackNet, "_get_req")
    def test_get_network_with_subnet2(self, m):
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE", "subnets": [2]},
             "subnet": ["FOO"]}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network(None, 1)
        self.assertEqual("ACTIVE", ret["status"])
        self.assertEqual([2], ret["subnets"])
        self.assertEqual(["FOO"], ret["subnet_info"])
        m.assert_called_with(req_mock, method="GET",
                             path="/subnets/2", query_string=None)

    @mock.patch.object(helpers.OpenStackNet, "_make_create_request")
    def test_create_only_network(self, m):
        name = "name_net"
        net_id = 1
        state = "ACTIVE"
        project = "project_id"
        parameters = {"occi.core.title": name,
                      "occi.core.id": net_id,
                      "occi.network.state": state,
                      "project": project,
                      }
        resp = fakes.create_fake_json_resp(
            {"network": {"network_id": net_id}}, 201)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.create_network(None, parameters)
        self.assertEqual(net_id, ret["network_id"])
        m.assert_called_with(None, "network", parameters)

    @mock.patch.object(helpers.OpenStackNet, "_make_create_request")
    def test_create_full_network(self, m):
        name = "name_net"
        net_id = 1
        state = "ACTIVE"
        project = "project_id"
        ip_version = "IPv4"
        cidr = "0.0.0.0"
        gate_way = "0.0.0.1"
        subnet_id = 11
        parameters = {"occi.core.title": name,
                      "occi.core.id": net_id,
                      "occi.network.state": state,
                      "X_PROJECT_ID": project,
                      "occi.network.ip_version": ip_version,
                      "occi.networkinterface.address": cidr,
                      "occi.networkinterface.gateway": gate_way
                      }
        resp = fakes.create_fake_json_resp(
            {"network": {"id": net_id},
             "subnet": {"id": subnet_id}}, 201
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.create_network(None, parameters)
        self.assertEqual(net_id, ret["id"])
        ret2 = self.helper.create_subnet(None, parameters)
        self.assertEqual(subnet_id, ret2["id"])
        m.assert_called_with(None, "subnet", parameters)

    @mock.patch.object(helpers.OpenStackNet, "_get_req")
    def test_create_full_network_2(self, m):
        name = "name_net"
        net_id = 1
        state = "ACTIVE"
        project = "project_id"
        ip_version = 4
        cidr = "0.0.0.0"
        gate_way = "0.0.0.1"
        subnet_id = 11
        parameters = {"occi.core.title": name,
                      "occi.core.id": net_id,
                      "occi.network.state": state,
                      "X_PROJECT_ID": project,
                      "occi.network.ip_version": ip_version,
                      "occi.networkinterface.address": cidr,
                      "occi.networkinterface.gateway": gate_way
                      }
        resp = fakes.create_fake_json_resp(
            {"network": {"id": net_id},
             "subnet": {"id": subnet_id}}, 201
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.create_network(None, parameters)
        self.assertEqual(net_id, ret["id"])
        ret2 = self.helper.create_subnet(None, parameters)
        self.assertEqual(subnet_id, ret2["id"])
        param = parsers.translate_parameters(
            self.translation["subnet"], parameters)
        m.assert_called_with(None,
                             path="/subnets",
                             content_type="application/json",
                             body=json.dumps(parsers.make_body(
                                 "subnet", param)),
                             method="POST")

    @mock.patch.object(helpers.OpenStackNet, "_make_delete_request")
    def test_delete_network(self, m):
        resp = fakes.create_fake_json_resp({"network": []}, 204)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.delete_network(None, 1)
        self.assertEqual(ret.status_int, 204)
        m.assert_called_with(None, "/networks", 1)

    @mock.patch.object(helpers.OpenStackNet, "_get_req")
    def test_delete_network2(self, m):
        resp = fakes.create_fake_json_resp({"network": []}, 204)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        parameters = {"occi.core.id": 1}
        ret = self.helper.delete_network(None, parameters)
        self.assertEqual(ret.status_int, 204)
        m.assert_called_with(None, method="DELETE",
                             path="/networks/1")