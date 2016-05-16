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

from ooi.api import helpers_neutron
from ooi import exception
from ooi.tests import base
from ooi.tests import fakes_network as fakes
from ooi import utils


class TestNetOpenStackHelper(base.TestCase):
    def setUp(self):
        super(TestNetOpenStackHelper, self).setUp()
        self.version = "version foo bar baz"
        self.helper = helpers_neutron.OpenStackNeutron(self.version)
        self.translation = {"networks": {"occi.core.title": "name"
                                         },
                            "subnets": {"occi.core.id": "network_id",
                                        "org.openstack.network.ip_version":
                                            "ip_version",
                                        "occi.network.address": "cidr",
                                        "occi.network.gateway":
                                            "gateway_ip"
                                        }
                            }

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_make_get_request")
    def test_index(self, m):
        resp = fakes.create_fake_json_resp({"networks": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.list_resources(None, 'networks', None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None, "/networks", None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_req")
    def test_get_list_with_public(self, m):
        id_public = uuid.uuid4().hex
        id_private = uuid.uuid4().hex
        net_private = {"status": "ACTIVE", "id": id_private}
        net_public = {"status": "ACTIVE", "id": id_public,
                      'router:external': True}
        resp = fakes.create_fake_json_resp({
            "networks": [net_private, net_public]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.list_networks(None, None)
        self.assertEqual(2, ret.__len__())
        self.assertEqual(id_private, ret[0]['id'])
        self.assertEqual('PUBLIC', ret[1]['id'])
        m.assert_called_with(None, method="GET",
                             path="/networks", query_string=None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_req")
    def test_index_req(self, m):
        resp = fakes.create_fake_json_resp({"networks": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.list_resources(None, 'networks', None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None, method="GET",
                             path="/networks", query_string=None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_make_get_request")
    def test_index3(self, m):
        id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp({"networks": [{"id": id}]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.list_networks(None, None)
        self.assertEqual(id, ret[0]['id'])
        m.assert_called_with(None, "/networks", None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_make_get_request")
    def test_get_network(self, m):
        id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE", "id": id}}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network_details(None, id)
        self.assertEqual("active", ret["state"])
        m.assert_called_with(None, "/networks/%s" % id)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_req")
    def test_get_network_public(self, m):
        id = 'PUBLIC'
        resp_get_public = fakes.create_fake_json_resp(
            {"networks": [{"status": "ACTIVE", "id": id}]}, 200)
        req_mock_public = mock.MagicMock()
        req_mock_public.get_response.return_value = resp_get_public
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE", "id": id}}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.side_effect = [req_mock_public, req_mock]
        ret = self.helper.get_network_details(None, id)
        self.assertEqual("active", ret["state"])
        m.assert_called_with(None, method="GET",
                             path="/networks/%s" % id,
                             query_string=None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_req")
    def test_get_network_req(self, m):
        id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE", "id": id}}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network_details(None, id)
        self.assertEqual("active", ret["state"])
        m.assert_called_with(None, method="GET",
                             path="/networks/%s" % id,
                             query_string=None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_make_get_request")
    def test_get_subnetwork(self, m):
        id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"subnet": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_resource(None, 'subnets', id)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None, "/subnets/%s" % id)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_make_get_request")
    def test_get_network_with_subnet(self, m):
        id = uuid.uuid4().hex
        address = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "ACTIVE", "id": id, "subnets": [2]},
             "subnet": {"cidr": address}}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network_details(None, id)
        self.assertEqual("active", ret["state"])
        self.assertEqual(address, ret["address"])
        m.assert_called_with(req_mock, "/subnets/2")

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_req")
    def test_get_network_with_subnet2(self, m):
        id = uuid.uuid4().hex
        address = '90349034'
        resp = fakes.create_fake_json_resp(
            {"network": {"status": "DOWN", "id": id, "subnets": [2]},
             "subnet": {"cidr": address}}, 200
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_network_details(None, id)
        self.assertEqual("inactive", ret["state"])
        self.assertEqual(address, ret["address"])
        m.assert_called_with(req_mock, method="GET",
                             path="/subnets/2", query_string=None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "_make_create_request")
    def test_create_only_network(self, m):
        name = "name_net"
        net_id = uuid.uuid4().hex
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
        ret = self.helper.create_resource(None, 'networks', parameters)
        self.assertEqual(net_id, ret["network_id"])
        m.assert_called_with(None, "networks", parameters)

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "_make_create_request")
    def test_create_resource_net_subnet(self, m):
        name = "name_net"
        net_id = uuid.uuid4().hex
        state = "ACTIVE"
        project = "project_id"
        ip_version = 4
        cidr = "0.0.0.0"
        gate_way = "0.0.0.1"
        subnet_id = uuid.uuid4().hex
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
        ret = self.helper.create_resource(None, 'networks', parameters)
        self.assertEqual(net_id, ret["id"])
        ret2 = self.helper.create_resource(None, 'subnets', parameters)
        self.assertEqual(subnet_id, ret2["id"])
        m.assert_called_with(None, "subnets", parameters)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_req")
    def test_create_resource_net_subnet_req(self, m):
        name = "name_net"
        net_id = uuid.uuid4().hex
        state = "ACTIVE"
        project = "project_id"
        ip_version = uuid.uuid4().hex
        cidr = "0.0.0.0"
        gate_way = "0.0.0.1"
        subnet_id = uuid.uuid4().hex
        parameters = {"occi.core.title": name,
                      "occi.core.id": net_id,
                      "occi.network.state": state,
                      "X_PROJECT_ID": project,
                      "org.openstack.network.ip_version": ip_version,
                      "occi.network.address": cidr,
                      "occi.network.gateway": gate_way
                      }
        resp = fakes.create_fake_json_resp(
            {"network": {"id": net_id},
             "subnet": {"id": subnet_id}}, 201
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.create_resource(None, 'networks', parameters)
        self.assertEqual(net_id, ret["id"])
        ret2 = self.helper.create_resource(None, 'subnets', parameters)
        self.assertEqual(subnet_id, ret2["id"])
        m.assert_called_with(None,
                             path="/subnets",
                             content_type="application/json",
                             body=json.dumps(utils.make_body(
                                 "subnet", parameters)),
                             method="POST")

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_make_put_request")
    def test_add_router_interface(self, m):
        router_id = uuid.uuid4().hex
        subnet_id = uuid.uuid4().hex
        port_id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"port_id": port_id, "subnet_id": subnet_id}, 201
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper._add_router_interface(None, router_id, subnet_id)
        self.assertEqual(port_id, ret["port_id"])
        self.assertEqual(subnet_id, ret["subnet_id"])
        path = "/routers/%s/add_router_interface" % router_id
        param = {"subnet_id": subnet_id}
        m.assert_called_with(None, path, param)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_make_put_request")
    def test_remove_router_interface(self, m):
        router_id = uuid.uuid4().hex
        subnet_id = uuid.uuid4().hex
        port_id = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"port_id": port_id, "subnet_id": subnet_id}, 201
        )
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper._remove_router_interface(None, router_id, port_id)
        self.assertEqual(port_id, ret["port_id"])
        self.assertEqual(subnet_id, ret["subnet_id"])
        path = "/routers/%s/remove_router_interface" % router_id
        param = {"port_id": port_id}
        m.assert_called_with(None, path, param)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    def test_get_public_network(self, m):
        public_id = uuid.uuid4().hex
        m.return_value = [{"id": public_id}]
        ret = self.helper._get_public_network(None)
        att_public = {"router:external": True}
        self.assertEqual(public_id, ret)
        m.assert_called_with(None, 'networks', att_public)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "create_resource")
    def test_add_floating_ip(self, m):
        port_id = uuid.uuid4().hex
        public_net = uuid.uuid4().hex
        f_ip = uuid.uuid4().hex
        ip = '0.0.0.1'
        m.return_value = {"id": f_ip,
                          'floating_ip_address': ip}
        ret = self.helper._add_floating_ip(None, public_net, port_id)
        attributes_port = {
            "floating_network_id": public_net,
            "port_id": port_id
        }
        self.assertEqual(f_ip, ret['id'])
        self.assertEqual(ip, ret['floating_ip_address'])
        m.assert_called_with(None, 'floatingips', attributes_port)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "delete_resource")
    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    def test_remove_floating_ip(self, m_list, m_del):
        ip = '1.0.0.0'
        public_net = uuid.uuid4().hex
        f_ip = uuid.uuid4().hex
        m_list.return_value = [{'id': f_ip}]
        m_del.return_value = []
        ret = self.helper._remove_floating_ip(None, public_net, ip)
        attributes_port = {
            "floating_network_id": public_net,
            "floating_ip_address": ip
        }
        self.assertEqual([], ret)
        m_list.assert_called_with(None, 'floatingips', attributes_port)
        m_del.assert_called_with(None, 'floatingips', f_ip)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "create_resource")
    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "_add_router_interface")
    def test_create_full_network(self, add_if, list_net, cre_net):
        name = "name_net"
        net_id = uuid.uuid4().hex
        subnet_id = uuid.uuid4().hex
        router_id = uuid.uuid4().hex
        public_net = uuid.uuid4().hex
        state = "ACTIVE"
        ip_version = 4
        cidr = "0.0.0.0/24"
        gate_way = "0.0.0.1"
        parameters = {"occi.core.title": name,
                      "occi.core.id": net_id,
                      "occi.network.state": state,

                      "org.openstack.network.ip_version": ip_version,
                      "occi.network.address": cidr,
                      "occi.network.gateway": gate_way
                      }
        cre_net.side_effect = [{'id': net_id,
                                "status": 'active',
                                "name": 'xx'},
                               {"id": subnet_id,
                                "cidr": cidr,
                                "gateway_ip": gate_way,
                                },
                               {"id": router_id},
                               {"id": 0}]
        list_net.return_value = [{'id': public_net}]
        ret = self.helper.create_network(None, parameters)
        self.assertEqual(net_id, ret["id"])
        param = utils.translate_parameters(
            self.translation["networks"], parameters)
        self.assertEqual((None, 'networks',
                          param),
                         cre_net.call_args_list[0][0])
        param_subnet = utils.translate_parameters(
            self.translation["subnets"], parameters)
        param_subnet['network_id'] = net_id
        self.assertEqual((None, 'subnets',
                          param_subnet),
                         cre_net.call_args_list[1][0])
        self.assertEqual((None, 'routers',
                          {'external_gateway_info': {
                              'network_id': public_net
                          }
                          }),
                         cre_net.call_args_list[2][0])
        add_if.assert_called_with(None, router_id, subnet_id)
        self.assertEqual(cidr, ret['address'])
        self.assertEqual(gate_way, ret['gateway'])

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "delete_resource")
    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "_remove_router_interface")
    def test_delete_network(self, m_if, m_list, m_del):
        net_id = uuid.uuid4().hex
        router_id = uuid.uuid4().hex
        m_del.side_effect = [{0},
                             {0},
                             {0},
                             ]
        port1 = {'id': 1,
                 'device_owner': 'network:router_interface',
                 'device_id': router_id
                 }
        port2 = {'id': 2, 'device_owner': 'nova'}
        m_list.return_value = [port1, port2]
        m_del.side_effect = [{0}, {0}, []]
        m_if.return_value = []
        ret = self.helper.delete_network(None, net_id)
        self.assertEqual(ret, [])
        self.assertEqual((None, 'routers',
                          port1['device_id']),
                         m_del.call_args_list[0][0])
        self.assertEqual((None, 'ports',
                          port2['id']),
                         m_del.call_args_list[1][0])
        self.assertEqual((None, 'networks',
                          net_id),
                         m_del.call_args_list[2][0])

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "_make_delete_request")
    def test_delete_network_resource_make_mock(self, m):
        resp = fakes.create_fake_json_resp({"network": []}, 204)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.delete_resource(None, 'networks', 1)
        self.assertEqual(ret, [])
        m.assert_called_with(None, "/networks", 1)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_req")
    def test_response_delete_network_resource(self, m):
        resp = fakes.create_fake_json_resp({"network": []}, 204)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        id = 1
        ret = self.helper.delete_resource(None, 'networks', id)
        self.assertEqual(ret, [])
        m.assert_called_with(None, method="DELETE",
                             path="/networks/1")

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_public_network")
    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_add_floating_ip")
    def test_assign_floating_ip(self, m_add, m_list, m_get_net):
        compute_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        param_occi = {'occi.core.target': net_id,
                      'occi.core.source': compute_id
                      }
        f_id = uuid.uuid4().hex
        ip = '0.0.0.1'
        port = {'id': 11, 'network_id': net_id,
                'device_owner': 'nova'}
        param = {'device_id': compute_id}
        m_get_net.return_value = net_id
        m_list.return_value = [port]
        m_add.return_value = {"id": f_id,
                              'floating_ip_address': ip,
                              'floating_network_id': '84'}
        ret = self.helper.assign_floating_ip(None, param_occi)
        self.assertEqual(net_id, ret['network_id'])
        self.assertEqual(ip, ret['ip'])
        m_list.assert_called_with(None, 'ports', param)
        m_add.assert_called_with(None, net_id, port['id'])

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_get_public_network")
    @mock.patch.object(helpers_neutron.OpenStackNeutron, "_remove_floating_ip")
    def test_release_floating_ip(self, m_add, m_get_net):
        ip = '22.0.0.1'
        net_id = 'PUBLIC'
        iface = {'net_id': net_id,
                 'ip': ip}
        m_get_net.return_value = net_id
        m_add.return_value = []
        ret = self.helper.release_floating_ip(None, iface)
        self.assertEqual([], ret)
        m_add.assert_called_with(None, net_id, ip)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "create_resource")
    def test_create_port(self, m_create):
        ip = '22.0.0.1'
        net_id = uuid.uuid4().hex
        mac = '890234'
        device_id = uuid.uuid4().hex
        p = {"network_id": net_id, 'device_id': device_id,
             "fixed_ips": [{"ip_address": ip}],
             "mac_address": mac, "status": "ACTIVE"
             }
        m_create.return_value = p
        ret = self.helper.create_port(None, {'sa': 1})
        self.assertEqual(device_id, ret['compute_id'])
        self.assertEqual(ip, ret['ip'])
        self.assertEqual(net_id, ret['network_id'])
        self.assertEqual(mac, ret['mac'])

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    @mock.patch.object(helpers_neutron.OpenStackNeutron, "delete_resource")
    def test_delete_port(self, m_delete, m_list):
        port_id = uuid.uuid4().hex
        p = [{'id': port_id}]
        m_list.return_value = p
        m_delete.return_value = []
        iface = {'compute_id': None,
                 'mac': None}
        ret = self.helper.delete_port(None, iface)
        self.assertEqual([], ret)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "list_resources")
    def test_list_port_not_found(self, m_list):
        iface = {'compute_id': None,
                 'mac': None}
        m_list.return_value = []
        self.assertRaises(exception.LinkNotFound,
                          self.helper.delete_port,
                          None,
                          iface)
