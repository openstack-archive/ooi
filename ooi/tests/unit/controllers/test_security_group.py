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

import mock

from ooi.api import helpers_neutron
from ooi.api import securitygroup as security_group_api
from ooi import exception
from ooi.occi.infrastructure import securitygroup as occi_security_group
from ooi.openstack import helpers as openstack_helper
from ooi.tests import base
from ooi.tests import fakes_network as fakes


class TestSecurityGroupControllerNeutron(base.TestController):

    def setUp(self):
        super(TestSecurityGroupControllerNeutron, self).setUp()
        self.controller = security_group_api.Controller(
            neutron_ooi_endpoint="ff")

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "list_security_groups")
    def test_list_security_group(self, m_list):
        tenant_id = fakes.tenants["baz"]["id"]
        sec_group = openstack_helper.build_security_group_from_neutron(
            fakes.security_groups[tenant_id]
        )
        req = fakes.create_req_test(None, None)
        m_list.return_value = sec_group
        result = self.controller.index(req)
        expected = self.controller._get_security_group_resources(sec_group)
        self.assertEqual(result.resources.__len__(),
                         expected.__len__())
        for r in result.resources:
            self.assertIsInstance(r, occi_security_group.SecurityGroupResource)
        m_list.assert_called_with(req)

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "list_security_groups")
    def test_list_security_group_empty(self, m_list):
        tenant_id = fakes.tenants["foo"]["id"]
        sec_group = openstack_helper.build_security_group_from_neutron(
            fakes.security_groups[tenant_id]
        )
        req = fakes.create_req_test(None, None)
        m_list.return_value = sec_group
        result = self.controller.index(req)
        self.assertEqual(result.resources.__len__(), 0)

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "get_security_group_details")
    def test_show_security_group(self, m_list):
        tenant_id = fakes.tenants["baz"]["id"]
        sec_group = openstack_helper.build_security_group_from_neutron(
            [fakes.security_groups[tenant_id][0]]
        )
        req = fakes.create_req_test(None, None)
        m_list.return_value = sec_group[0]
        result = self.controller.show(req, None)
        expected = self.controller._get_security_group_resources(sec_group)[0]
        self.assertIsInstance(
            result,
            occi_security_group.SecurityGroupResource)
        self.assertEqual(result, expected)
        m_list.assert_called_with(req, None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "get_resource")
    def test_show_security_group_not_found(self, m_list):
        tenant_id = fakes.tenants["baz"]["id"]
        sec_group = openstack_helper.build_security_group_from_neutron(
            fakes.security_groups[tenant_id]
        )
        m_list.return_value = sec_group
        req = fakes.create_req_test(None, None)
        self.assertRaises(exception.NotFound,
                          self.controller.show,
                          req,
                          None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron, "delete_resource")
    def test_delete_security_group(self, m_list):
        m_list.return_value = None
        ret = self.controller.delete(None, None)
        self.assertIsNone(ret)
        m_list.assert_called_with(None, 'security-groups', None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "delete_security_group")
    def test_delete_security_group_not_found(self, m_list):
        m_list.side_effect = exception.NotFound
        req = fakes.create_req_test(None, None)
        self.assertRaises(exception.NotFound,
                          self.controller.delete,
                          req,
                          None)

    @mock.patch.object(helpers_neutron.OpenStackNeutron,
                       "create_security_group")
    def test_create_security_groups(self, m_create):
        tenant_id = fakes.tenants["baz"]["id"]
        sec_group = openstack_helper.build_security_group_from_neutron(
            fakes.security_groups[tenant_id]
        )[0]
        params = {"occi.core.title": sec_group["title"],
                  "occi.securitygroup.rules": sec_group["rules"],
                  "occi.core.summary": sec_group["summary"]
                  }
        categories = {occi_security_group.SecurityGroupResource.kind}
        req = fakes.create_req_json_occi(params, categories)
        m_create.return_value = sec_group
        ret = self.controller.create(req, params)
        expected = self.controller._get_security_group_resources(
            [sec_group])
        self.assertIsInstance(ret.resources[0],
                              occi_security_group.SecurityGroupResource)
        self.assertEqual(expected[0], ret.resources[0])
        m_create.assert_called_with(req, sec_group["title"],
                                    sec_group["summary"],
                                    sec_group["rules"])

    def test_create_error(self):
        test_networks = fakes.networks[fakes.tenants["foo"]["id"]]
        schema1 = occi_security_group.SecurityGroupResource.kind.scheme
        net = test_networks[0]
        schemes = {schema1: net}
        parameters = {"occi.core.title": "name"}
        req = fakes.create_req_test(parameters, schemes)

        self.assertRaises(exception.Invalid, self.controller.create, req)

    def test_create_invalid_param_rule(self):
        params = {"occi.core.title": "group",
                  "occi.securitygroup.rules": "{'wrong': 'value'}]"
                  }
        categories = {occi_security_group.SecurityGroupResource.kind}
        req = fakes.create_req_test_occi(params, categories)
        self.assertRaises(exception.Invalid, self.controller.create, req)
