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

import mock

from ooi.api import helpers
from ooi.api import query
from ooi.occi.core import entity
from ooi.occi.core import link
from ooi.occi.core import resource
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import contextualization
from ooi.occi.infrastructure import ip_reservation
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link
from ooi.occi.infrastructure import templates as infra_templates
from ooi.openstack import contextualization as os_contextualization
from ooi.openstack import network as os_network
from ooi.openstack import templates
from ooi.tests import base
from ooi.tests import fakes


class TestQueryController(base.TestController):
    def setUp(self):
        super(TestQueryController, self).setUp()
        self.controller = query.Controller(mock.MagicMock(), None)

    @mock.patch.object(query.Controller, "_os_tpls")
    @mock.patch.object(query.Controller, "_resource_tpls")
    @mock.patch.object(query.Controller, "_ip_pools")
    def test_index(self, m_res, m_os, m_pools):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])

        f = fakes.flavors[1]
        res_tpl = templates.OpenStackResourceTemplate(f["id"], f["name"],
                                                      f["vcpus"], f["ram"],
                                                      f["disk"])
        m_res.return_value = [res_tpl]
        i = fakes.images["foo"]
        os_tpl = templates.OpenStackOSTemplate(i["id"], i["name"])
        m_os.return_value = [os_tpl]
        ip_pool = os_network.OSFloatingIPPool("foo")
        m_pools.return_value = [ip_pool]

        expected_kinds = [
            entity.Entity.kind,
            resource.Resource.kind,
            link.Link.kind,
            compute.ComputeResource.kind,
            storage.StorageResource.kind,
            storage_link.StorageLink.kind,
            network.NetworkResource.kind,
            network_link.NetworkInterface.kind,
            ip_reservation.IPReservation.kind,
        ]

        expected_mixins = [
            res_tpl,
            os_tpl,
            ip_pool,
            network.ip_network,
            network_link.ip_network_interface,
            infra_templates.os_tpl,
            infra_templates.resource_tpl,
            os_contextualization.user_data,
            os_contextualization.public_key,
            contextualization.user_data,
            contextualization.ssh_key,
        ]

        expected_actions = [
            compute.start,
            compute.stop,
            compute.restart,
            compute.suspend,
            compute.save,

            storage.online,
            storage.offline,
            storage.backup,
            storage.snapshot,
            storage.resize,

            network.up,
            network.down,
        ]

        ret = self.controller.index(req)
        self.assertItemsEqual(expected_kinds, ret.kinds)
        self.assertItemsEqual(expected_mixins, ret.mixins)
        self.assertItemsEqual(expected_actions, ret.actions)
        self.assertEqual([], ret.resources)
        self.assertEqual([], ret.links)

    @mock.patch.object(query.Controller, "_os_tpls")
    @mock.patch.object(query.Controller, "_resource_tpls")
    @mock.patch.object(query.Controller, "_ip_pools")
    def test_index_neutron(self, m_res, m_os, m_pools):
        neutron_controller = query.Controller(mock.MagicMock(),
                                              None, "http://foo")
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])

        f = fakes.flavors[1]
        res_tpl = templates.OpenStackResourceTemplate(f["id"], f["name"],
                                                      f["vcpus"], f["ram"],
                                                      f["disk"])
        m_res.return_value = [res_tpl]
        i = fakes.images["foo"]
        os_tpl = templates.OpenStackOSTemplate(i["id"], i["name"])
        m_os.return_value = [os_tpl]
        ip_pool = os_network.OSFloatingIPPool("foo")
        m_pools.return_value = [ip_pool]

        expected_kinds = [
            entity.Entity.kind,
            resource.Resource.kind,
            link.Link.kind,
            compute.ComputeResource.kind,
            storage.StorageResource.kind,
            storage_link.StorageLink.kind,
            network.NetworkResource.kind,
            network_link.NetworkInterface.kind,
            ip_reservation.IPReservation.kind,
        ]

        expected_mixins = [
            res_tpl,
            os_tpl,
            ip_pool,
            os_network.neutron_network,
            network.ip_network,
            network_link.ip_network_interface,
            infra_templates.os_tpl,
            infra_templates.resource_tpl,
            os_contextualization.user_data,
            os_contextualization.public_key,
            contextualization.user_data,
            contextualization.ssh_key,
        ]

        expected_actions = [
            compute.start,
            compute.stop,
            compute.restart,
            compute.suspend,
            compute.save,

            storage.online,
            storage.offline,
            storage.backup,
            storage.snapshot,
            storage.resize,

            network.up,
            network.down,
        ]

        ret = neutron_controller.index(req)
        self.assertItemsEqual(expected_kinds, ret.kinds)
        self.assertItemsEqual(expected_mixins, ret.mixins)
        self.assertItemsEqual(expected_actions, ret.actions)
        self.assertEqual([], ret.resources)
        self.assertEqual([], ret.links)

    @mock.patch.object(helpers.OpenStackHelper, "get_flavors")
    def test_get_resource_tpls(self, m_get_flavors):
        m_get_flavors.return_value = fakes.flavors.values()
        ret = self.controller._resource_tpls(None)
        expected = []
        for f in fakes.flavors.values():
            expected.append(
                templates.OpenStackResourceTemplate(f["id"], f["name"],
                                                    f["vcpus"], f["ram"],
                                                    f["disk"])
            )
        # FIXME(aloga): this won't work until we create the correct equality
        # functions
        # self.assertItemsEqual(expected, ret)
        for i in range(len(expected)):
            self.assertEqual(expected[i].title, ret[i].title)

    @mock.patch.object(helpers.OpenStackHelper, "get_flavors")
    def test_get_resource_tpls_empty(self, m_get_flavors):
        m_get_flavors.return_value = []
        ret = self.controller._resource_tpls(None)
        expected = []
        self.assertEqual(expected, ret)

    @mock.patch.object(helpers.OpenStackHelper, "get_images")
    def test_get_os_tpls(self, m_get_images):
        m_get_images.return_value = fakes.images.values()
        ret = self.controller._os_tpls(None)
        expected = []
        for i in fakes.images.values():
            expected.append(
                templates.OpenStackOSTemplate(i["id"], i["name"]),
            )
        # FIXME(aloga): this won't work until we create the correct equality
        # functions
        # self.assertItemsEqual(expected, ret)
        for i in range(len(expected)):
            self.assertEqual(expected[i].title, ret[i].title)

    @mock.patch.object(helpers.OpenStackHelper, "get_images")
    def test_get_os_tpls_empty(self, m_get_images):
        m_get_images.return_value = []
        ret = self.controller._os_tpls(None)
        expected = []
        self.assertEqual(expected, ret)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_get_ip_pools(self, m_get_pools):
        for tenant in fakes.tenants.values():
            pools = fakes.pools[tenant["id"]]
            m_get_pools.return_value = pools
            expected = [os_network.OSFloatingIPPool(p['id']) for p in pools]
            ret = self.controller._ip_pools(None)
            # FIXME(aloga): this won't work til we create the correct equality
            # functions
            # self.assertItemsEqual(expected, ret)
            for i in range(len(expected)):
                self.assertEqual(expected[i].title, ret[i].title)

    @mock.patch.object(helpers.OpenStackHelper, "get_floating_ip_pools")
    def test_get_ip_pools_empty(self, m_get_pools):
        m_get_pools.return_value = []
        ret = self.controller._ip_pools(None)
        expected = []
        self.assertEqual(expected, ret)
