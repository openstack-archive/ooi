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

from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.occi.infrastructure import templates as occi_templates
from ooi.openstack import contextualization
from ooi.openstack import helpers
from ooi.openstack import network as os_network
from ooi.openstack import templates
from ooi.tests import base


class TestOpenStackOSTemplate(base.TestCase):
    def test_os_template(self):
        id = uuid.uuid4().hex
        title = "Frobble Image"
        location = "%s/%s" % (occi_templates.os_tpl._location, id)

        tpl = templates.OpenStackOSTemplate(id,
                                            title)
        self.assertEqual(id, tpl.term)
        self.assertEqual(title, tpl.title)
        self.assertTrue(tpl.scheme.startswith(helpers._PREFIX))
        self.assertIn(occi_templates.os_tpl, tpl.related)
        self.assertEqual(location, tpl.location)


class TestOpenStackResourceTemplate(base.TestCase):
    def test_resource_template(self):
        id = uuid.uuid4().hex
        name = "m1.humongous"
        cores = 10
        memory = 30
        disk = 40
        swap = 20
        ephemeral = 50
        location = "%s/%s" % (occi_templates.resource_tpl._location, id)

        tpl = templates.OpenStackResourceTemplate(id,
                                                  name,
                                                  cores,
                                                  memory,
                                                  disk,
                                                  swap=swap,
                                                  ephemeral=ephemeral)

        self.assertEqual(id, tpl.term)
        self.assertEqual("Flavor: %s" % name, tpl.title)
        self.assertTrue(tpl.scheme.startswith(helpers._PREFIX))
        self.assertIn(occi_templates.resource_tpl, tpl.related)
        self.assertEqual(cores, tpl.cores)
        self.assertEqual(memory, tpl.memory)
        self.assertEqual(disk, tpl.disk)
        self.assertEqual(swap, tpl.swap)
        self.assertEqual(ephemeral, tpl.ephemeral)
        self.assertEqual(name, tpl.name)
        self.assertEqual(location, tpl.location)


class TestHelpers(base.TestCase):
    def test_vm_state(self):
        self.assertEqual("active", helpers.vm_state("ACTIVE"))
        self.assertEqual("suspended", helpers.vm_state("SUSPENDED"))
        self.assertEqual("inactive", helpers.vm_state("PAUSED"))
        self.assertEqual("inactive", helpers.vm_state("STOPPED"))
        self.assertEqual("inactive", helpers.vm_state("BUILDING"))

    def test_vol_state(self):
        self.assertEqual("online", helpers.vol_state("in-use"))


class TestOpenStackUserData(base.TestCase):
    def test_os_userdata(self):
        user_data = "foobar"

        mxn = contextualization.OpenStackUserData(user_data)

        self.assertEqual("user_data", mxn.term)
        self.assertTrue(mxn.scheme.startswith(helpers._PREFIX))
        self.assertEqual(user_data, mxn.user_data)


class TestOpenStackPublicKey(base.TestCase):
    def test_os_userdata(self):
        key_name = "foobar"
        key_data = "1234"

        mxn = contextualization.OpenStackPublicKey(key_name, key_data)

        self.assertEqual("public_key", mxn.term)
        self.assertTrue(mxn.scheme.startswith(helpers._PREFIX))
        self.assertEqual(key_name, mxn.name)
        self.assertEqual(key_data, mxn.data)


class TestOSNetworkInterface(base.TestCase):
    def test_osnetwork_interface(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        n = network.NetworkResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        i = os_network.OSNetworkInterface(c, n, "00:01:02:03:04:05",
                                          "127.0.0.1", pool="foo")
        self.assertEqual('_'.join([c.id, n.id, "127.0.0.1"]), i.id)
        self.assertEqual(i.address, "127.0.0.1")
        self.assertEqual(i.interface, "eth0")
        self.assertEqual(i.mac, "00:01:02:03:04:05")
        self.assertEqual(i.state, "active")
        self.assertIsNone(i.gateway)
        self.assertEqual(network_link.NetworkInterface.kind, i.kind)
        self.assertEqual(2, len(i.mixins))
        self.assertIn(network_link.ip_network_interface, i.mixins)
        # FIXME(enolfc): this won't work without proper object comparison
        # self.assertIn(p, i.mixins)
        has_pool = False
        for m in i.mixins:
            if isinstance(m, os_network.OSFloatingIPPool):
                self.assertEqual(m.term, "foo")
                has_pool = True
                break
        self.assertTrue(has_pool)
        # contains kind and mixins attributes
        for att in network_link.NetworkInterface.kind.attributes:
            self.assertIn(att, i.attributes)
        for att in network_link.ip_network_interface.attributes:
            self.assertIn(att, i.attributes)

    def test_setters(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        n = network.NetworkResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        i = os_network.OSNetworkInterface(c, n, "00:01:02:03:04:05",
                                          "127.0.0.1")
        i.address = "192.163.1.2"
        self.assertEqual(
            "192.163.1.2", i.attributes["occi.networkinterface.address"].value)
        i.gateway = "192.163.1.1"
        self.assertEqual(
            "192.163.1.1", i.attributes["occi.networkinterface.gateway"].value)
        i.allocation = "static"
        self.assertEqual(
            "static", i.attributes["occi.networkinterface.allocation"].value)

    def test_getters(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        n = network.NetworkResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        i = os_network.OSNetworkInterface(c, n, "00:01:02:03:04:05",
                                          "127.0.0.1")
        i.attributes["occi.networkinterface.address"].value = "192.163.1.2"
        self.assertEqual("192.163.1.2", i.address)
        i.attributes["occi.networkinterface.gateway"].value = "192.163.1.1"
        self.assertEqual("192.163.1.1", i.gateway)
        i.attributes["occi.networkinterface.allocation"].value = "static"
        self.assertEqual("static", i.allocation)
