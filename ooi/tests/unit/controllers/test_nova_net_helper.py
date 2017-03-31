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

import json
import uuid

import mock

from ooi.api import helpers
from ooi.openstack import helpers as os_helpers
from ooi.tests import base
from ooi.tests import fakes as fakes_nova
from ooi.tests import fakes_network
from ooi import utils


class TestNovaNetOpenStackHelper(base.TestCase):
    def setUp(self):
        super(TestNovaNetOpenStackHelper, self).setUp()
        self.version = "version foo bar baz"
        self.helper = helpers.OpenStackHelper(None, self.version)

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_list_networks_with_public(self, m_t, m_rq):
        id = uuid.uuid4().hex
        resp = fakes_network.create_fake_json_resp(
            {"networks": [{"id": id}]},
            200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        resp_float = fakes_network.create_fake_json_resp(
            {"floating_ip_pools": [{"id": id}]}, 200
        )
        req_mock_float = mock.MagicMock()
        req_mock_float.get_response.return_value = resp_float
        m_rq.side_effect = [req_mock, req_mock_float]
        ret = self.helper.list_networks(None)
        self.assertEqual(2, ret.__len__())

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_list_networks_with_no_public(self, m_t, m_rq):
        id = uuid.uuid4().hex
        resp = fakes_network.create_fake_json_resp(
            {"networks": [{"id": id}]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        resp_float = fakes_network.create_fake_json_resp(
            {"floating_ip_pools": []}, 204
        )
        req_mock_float = mock.MagicMock()
        req_mock_float.get_response.return_value = resp_float
        m_rq.side_effect = [req_mock, req_mock_float]
        ret = self.helper.list_networks(None)
        self.assertEqual(1, ret.__len__())

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_list_networks(self, m_t, m_rq):
        id = uuid.uuid4().hex
        tenant_id = uuid.uuid4().hex
        m_t.return_value = tenant_id
        resp = fakes_network.create_fake_json_resp(
            {"networks": [{"id": id}]}, 200)
        resp_float = fakes_network.create_fake_json_resp(
            {"floating_ip_pools": [{"id": id}]}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        req_mock_float = mock.MagicMock()
        req_mock_float.get_response.return_value = resp_float
        m_rq.side_effect = [req_mock, req_mock_float]
        ret = self.helper.list_networks(None)
        self.assertEqual(id, ret[0]['id'])
        self.assertEqual(
            {'method': 'GET',
             'path': '/%s/os-networks' % (tenant_id)},
            m_rq.call_args_list[0][1]
        )
        self.assertEqual(
            {'method': 'GET',
             'path': '/%s/os-floating-ip-pools' % (tenant_id)},
            m_rq.call_args_list[1][1]
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
        resp = fakes_network.create_fake_json_resp(
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
        parameters = {"label": name,
                      "cidr": cidr,
                      "gateway": gateway
                      }
        resp = fakes_network.create_fake_json_resp(
            {"network": {"id": net_id, "label": name,
                         "cidr": cidr,
                         "gateway": gateway}}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_rq.return_value = req_mock
        ret = self.helper.create_network(None,
                                         name=name,
                                         cidr=cidr,
                                         gateway=gateway,
                                         )
        body = utils.make_body('network', parameters)
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

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_list_security_groups(self, m_t, m_rq):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        m_t.return_value = tenant_id
        sc_groups = fakes_nova.security_groups[tenant_id]
        resp = fakes_network.create_fake_json_resp(
            {"security_groups": sc_groups}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_rq.side_effect = [req_mock]
        ret = self.helper.list_security_groups(None)
        cont = 0
        for sc in sc_groups:
            self.assertEqual(sc['id'], ret[cont]['id'])
            cont = cont + 1
        self.assertEqual(
            {'method': 'GET',
             'path': '/%s/os-security-groups' % (tenant_id)},
            m_rq.call_args_list[0][1]
        )

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_delete_security_groups(self, m_t, m_rq):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        m_t.return_value = tenant_id
        sc_id = fakes_nova.security_groups[tenant_id][0]['id']
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = []
        m_rq.return_value = req_mock
        ret = self.helper.delete_security_group(None, sc_id)
        self.assertEqual(ret, [])
        m_rq.assert_called_with(
            None, method="DELETE",
            path="/%s/os-security-groups/%s" % (tenant_id, sc_id),
        )

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_get_security_group(self, m_t, m_rq):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        m_t.return_value = tenant_id
        sc_group = fakes_nova.security_groups[tenant_id][0]
        id = sc_group['id']
        m_t.return_value = tenant_id
        resp = fakes_network.create_fake_json_resp(
            {"security_group": sc_group}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_rq.return_value = req_mock
        ret = self.helper.get_security_group_details(None, id)
        self.assertEqual(sc_group['id'], ret["id"])
        self.assertEqual(sc_group['description'], ret["summary"])
        occi_os_group = os_helpers.build_security_group_from_nova(
            fakes_nova.security_groups[tenant_id]
        )[0]
        cont = 0
        for r in ret["rules"]:
            self.assertEqual(
                occi_os_group['rules'][cont]['protocol'], r["protocol"])
            self.assertEqual(
                occi_os_group['rules'][cont]['range'], r["range"])
            self.assertEqual(
                occi_os_group['rules'][cont]['port'], r["port"])
            self.assertEqual(
                occi_os_group['rules'][cont]['type'], r["type"])
            cont += 1

        m_rq.assert_called_with(
            None, method="GET",
            path="/%s/os-security-groups/%s" % (tenant_id, id),
        )

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_create_security_group(self, m_t, m_rq):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        m_t.return_value = tenant_id
        sc_group = fakes_nova.security_groups[tenant_id][0]
        occi_os_group = os_helpers.build_security_group_from_nova(
            fakes_nova.security_groups[tenant_id]
        )[0]
        resp = fakes_network.create_fake_json_resp(
            {"security_group": sc_group}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        resp_rule1 = fakes_network.create_fake_json_resp(
            {"security_group_rule": sc_group['rules'][0]}, 200
        )
        req_mock_rule1 = mock.MagicMock()
        req_mock_rule1.get_response.return_value = resp_rule1
        resp_rule2 = fakes_network.create_fake_json_resp(
            {"security_group_rule": sc_group['rules'][1]}, 200
        )
        req_mock_rule2 = mock.MagicMock()
        req_mock_rule2.get_response.return_value = resp_rule2
        m_rq.side_effect = [req_mock, req_mock_rule1, req_mock_rule2]
        ret = self.helper.create_security_group(
            None,
            name=occi_os_group['title'],
            description=occi_os_group['summary'],
            rules=occi_os_group['rules']
        )
        cont = 0
        for r in ret["rules"]:
            self.assertEqual(
                occi_os_group['rules'][cont]['protocol'], r["protocol"]
            )
            self.assertEqual(
                occi_os_group['rules'][cont]['range'], r["range"]
            )
            self.assertEqual(
                occi_os_group['rules'][cont]['port'], r["port"])
            self.assertEqual(
                occi_os_group['rules'][cont]['type'], r["type"])
            cont += 1

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_get_server_security_group(self, mock_tenant, mock_get):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        server_id = uuid.uuid4().hex
        sc_group = fakes_nova.security_groups[tenant_id]
        mock_tenant.return_value = tenant_id
        resp = fakes_network.create_fake_json_resp(
            {"security_groups": sc_group}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        mock_get.return_value = req_mock
        ret = self.helper._get_server_security_group(None, server_id)
        segroup = os_helpers.build_security_group_from_nova(
            sc_group
        )
        cont = 0
        for s in segroup:
            self.assertEqual(s, ret[cont])
            cont += 1
        mock_get.assert_called_with(
            None, method="GET",
            path="/%s/servers/%s/os-security-groups" % (tenant_id,
                                                        server_id),
        )

    @mock.patch.object(helpers.OpenStackHelper, "index")
    @mock.patch.object(helpers.OpenStackHelper, "_get_server_security_group")
    def test_list_server_security_links(self, mock_get, mock_list):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        servers = fakes_nova.servers[tenant_id]
        mock_list.return_value = servers
        sg = fakes_nova.security_groups[tenant_id]
        segroup = os_helpers.build_security_group_from_nova(sg)[0]
        mock_get.return_value = [segroup]
        ret = self.helper.list_server_security_links(None)
        cont = 0
        for server in servers:
            self.assertEqual(server["id"],
                             ret[cont]['compute_id'])
            self.assertEqual(segroup["title"],
                             ret[cont]['securitygroup']["title"])

            cont += 1

    @mock.patch.object(helpers.OpenStackHelper, "_get_server_security_group")
    def test_get_server_security_link(self, mock_get):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        server_id = uuid.uuid4().hex
        sg = fakes_nova.security_groups[tenant_id]
        segroup = os_helpers.build_security_group_from_nova(sg)[0]
        mock_get.return_value = [segroup]
        ret = self.helper.get_server_security_link(None, server_id,
                                                   segroup["id"])
        self.assertEqual(server_id,
                         ret[0]['compute_id'])
        self.assertEqual(segroup["title"],
                         ret[0]['securitygroup']["title"])

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_delete_server_security_link(self, mock_tenant, mock_req):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        server_id = uuid.uuid4().hex
        sg_name = "baz"
        mock_tenant.return_value = tenant_id
        sc_group = fakes_nova.security_groups[tenant_id][0]
        sg_name = sc_group["name"]
        resp_get = fakes_network.create_fake_json_resp(
            {"security_group": sc_group}, 200
        )
        req_mock_get = mock.MagicMock()
        req_mock_get.get_response.return_value = resp_get
        resp_cre = fakes_network.create_fake_json_resp(
            {}, 204
        )
        req_mock_del = mock.MagicMock()
        req_mock_del.get_response.return_value = resp_cre
        mock_req.side_effect = [req_mock_get, req_mock_del]
        ret = self.helper.delete_server_security_link(None,
                                                      server_id,
                                                      sg_name)
        self.assertEqual([], ret)
        mock_req.assert_called_with(
            None, method="POST",
            path="/%s/servers/%s/action" % (tenant_id,
                                            server_id),
            body='{"removeSecurityGroup": {"name": "%s"}}' % sg_name,
            content_type='application/json'

        )

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_create_server_security_link(self, mock_tenant, mock_req):
        tenant_id = fakes_nova.tenants["baz"]["id"]
        server_id = uuid.uuid4().hex
        sg_id = "baz"
        mock_tenant.return_value = tenant_id
        sc_group = fakes_nova.security_groups[tenant_id][0]
        resp_get = fakes_network.create_fake_json_resp(
            {"security_group": sc_group}, 200
        )
        req_mock_get = mock.MagicMock()
        req_mock_get.get_response.return_value = resp_get
        resp_create = fakes_network.create_fake_json_resp(
            {}, 204
        )
        req_mock_cre = mock.MagicMock()
        req_mock_cre.get_response.return_value = resp_create
        mock_req.side_effect = [req_mock_get, req_mock_cre]
        ret = self.helper.create_server_security_link(None,
                                                      server_id,
                                                      sg_id)
        self.assertEqual([], ret)
        sg_name = sc_group["name"]
        mock_req.assert_called_with(
            None, method="POST",
            path="/%s/servers/%s/action" % (tenant_id,
                                            server_id),
            body='{"addSecurityGroup": {"name": "%s"}}' % sg_name,
            content_type='application/json'

        )
