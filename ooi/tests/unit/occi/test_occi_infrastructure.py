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

from ooi.occi.core import link
from ooi.occi.core import mixin
from ooi.occi.core import resource
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link
from ooi.occi.infrastructure import templates
from ooi.tests import base


class TestOCCICompute(base.TestCase):
    def test_compute_class(self):
        c = compute.ComputeResource
        self.assertIn(compute.start, c.actions)
        self.assertIn(compute.stop, c.actions)
        self.assertIn(compute.suspend, c.actions)
        self.assertIn(compute.restart, c.actions)
        self.assertIn("occi.core.id", c.attributes)
        self.assertIn("occi.core.summary", c.attributes)
        self.assertIn("occi.core.title", c.attributes)
        self.assertIn("occi.compute.architecture", c.attributes)
        self.assertIn("occi.compute.cores", c.attributes)
        self.assertIn("occi.compute.hostname", c.attributes)
        self.assertIn("occi.compute.memory", c.attributes)
        self.assertIn("occi.compute.speed", c.attributes)
        self.assertIn("occi.compute.state", c.attributes)
        self.assertIn(resource.Resource.kind, c.kind.related)
        self.assertEqual(c.kind.location, "compute/")
        # TODO(aloga): We need to check that the attributes are actually set
        # after we get an object (we have to check this for this but also for
        # the other resources)

    def test_compute(self):
        id = uuid.uuid4().hex
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=id)
        self.assertEqual("foo", c.title)
        self.assertEqual(id, c.id)
        self.assertEqual("This is a summary", c.summary)
        self.assertIsNone(c.architecture)
        self.assertIsNone(c.cores)
        self.assertIsNone(c.hostname)
        self.assertIsNone(c.memory)
        self.assertIsNone(c.speed)

    def test_setters(self):
        c = compute.ComputeResource("foo")
        c.architecture = "bar"
        self.assertEqual("bar",
                         c.attributes["occi.compute.architecture"].value)
        c.cores = 5
        self.assertEqual(5, c.attributes["occi.compute.cores"].value)
        c.hostname = "foobar"
        self.assertEqual("foobar", c.attributes["occi.compute.hostname"].value)
        c.speed = 8
        self.assertEqual(8, c.attributes["occi.compute.speed"].value)
        c.memory = 4
        self.assertEqual(4, c.attributes["occi.compute.memory"].value)

    def test_getters(self):
        c = compute.ComputeResource("foo", state="baz")
        self.assertEqual("baz", c.state)
        c.attributes["occi.compute.architecture"].value = "bar"
        self.assertEqual("bar", c.architecture)
        c.attributes["occi.compute.cores"].value = 5
        self.assertEqual(5, c.cores)
        c.attributes["occi.compute.hostname"].value = "foobar"
        self.assertEqual("foobar", c.hostname)
        c.attributes["occi.compute.speed"].value = 8
        self.assertEqual(8, c.speed)
        c.attributes["occi.compute.memory"].value = 9
        self.assertEqual(9, c.memory)


class TestOCCIStorage(base.TestCase):
    def test_storage_class(self):
        s = storage.StorageResource
        self.assertIn(storage.online, s.actions)
        self.assertIn(storage.offline, s.actions)
        self.assertIn(storage.backup, s.actions)
        self.assertIn(storage.snapshot, s.actions)
        self.assertIn(storage.resize, s.actions)
        self.assertIn("occi.core.id", s.attributes)
        self.assertIn("occi.core.summary", s.attributes)
        self.assertIn("occi.core.title", s.attributes)
        self.assertIn("occi.storage.size", s.attributes)
        self.assertIn("occi.storage.state", s.attributes)
        self.assertIn(resource.Resource.kind, s.kind.related)
        self.assertEqual(s.kind.location, "storage/")
        # TODO(aloga): We need to check that the attributes are actually set
        # after we get an object (we have to check this for this but also for
        # the other resources)

    def test_storage(self):
        id = uuid.uuid4().hex
        s = storage.StorageResource("foo",
                                    summary="This is a summary",
                                    id=id)
        self.assertEqual("foo", s.title)
        self.assertEqual(id, s.id)
        self.assertEqual("This is a summary", s.summary)
        self.assertIsNone(s.size)
        self.assertIsNone(s.state)

    def test_setters(self):
        s = storage.StorageResource("foo")
        s.size = 3
        self.assertEqual(3, s.attributes["occi.storage.size"].value)

    def test_getters(self):
        s = storage.StorageResource("foo", size=5, state="foobar")
        self.assertEqual(5, s.size)
        self.assertEqual("foobar", s.state)


class TestOCCIStorageLink(base.TestCase):
    def test_storagelink_class(self):
        s = storage_link.StorageLink
        self.assertIn("occi.core.id", s.attributes)
        self.assertIn("occi.core.title", s.attributes)
        self.assertIn("occi.core.source", s.attributes)
        self.assertIn("occi.core.target", s.attributes)
        self.assertIn("occi.storagelink.mountpoint", s.attributes)
        self.assertIn("occi.storagelink.deviceid", s.attributes)
        self.assertIn("occi.storagelink.state", s.attributes)
        self.assertIn(link.Link.kind, s.kind.related)
        self.assertEqual(s.kind.location, "storagelink/")

    def test_storagelink(self):
        server_id = uuid.uuid4().hex
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=server_id)
        vol_id = uuid.uuid4().hex
        s = storage.StorageResource("bar",
                                    summary="This is a summary",
                                    id=vol_id)
        l = storage_link.StorageLink(c, s)
        link_id = '%s_%s' % (server_id, vol_id)
        self.assertEqual(link_id, l.id)
        self.assertIsNone(l.deviceid)
        self.assertIsNone(l.mountpoint)
        self.assertIsNone(l.state)

    def test_setters(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        s = storage.StorageResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        l = storage_link.StorageLink(c, s)
        l.deviceid = "/dev/vdc"
        self.assertEqual("/dev/vdc",
                         l.attributes["occi.storagelink.deviceid"].value)
        l.mountpoint = "/mnt"
        self.assertEqual("/mnt",
                         l.attributes["occi.storagelink.mountpoint"].value)

    def test_getters(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        s = storage.StorageResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        l = storage_link.StorageLink(c, s, deviceid="/dev/vdc",
                                     mountpoint="/mnt", state="foobar")
        self.assertEqual("/dev/vdc", l.deviceid)
        self.assertEqual("/mnt", l.mountpoint)
        self.assertEqual("foobar", l.state)


class TestTemplates(base.TestCase):
    def test_os_tpl(self):
        self.assertIsInstance(templates.os_tpl,
                              mixin.Mixin)
        self.assertEqual("os_tpl",
                         templates.os_tpl.term)

    def test_resource_tpl(self):
        self.assertIsInstance(templates.resource_tpl,
                              mixin.Mixin)
        self.assertEqual("resource_tpl",
                         templates.resource_tpl.term)


class TestOCCINetwork(base.TestCase):
    def test_network_class(self):
        n = network.NetworkResource
        self.assertIn(network.up, n.actions)
        self.assertIn(network.down, n.actions)
        self.assertIn("occi.core.id", n.attributes)
        self.assertIn("occi.core.summary", n.attributes)
        self.assertIn("occi.core.title", n.attributes)
        self.assertIn("occi.network.vlan", n.attributes)
        self.assertIn("occi.network.label", n.attributes)
        self.assertIn("occi.network.state", n.attributes)
        self.assertIn(resource.Resource.kind, n.kind.related)
        self.assertEqual(n.kind.location, "network/")
        # TODO(aloga): We need to check that the attributes are actually set
        # after we get an object (we have to check this for this but also for
        # the other resources)

    def test_network(self):
        id = uuid.uuid4().hex
        n = network.NetworkResource("foo",
                                    summary="This is a summary",
                                    id=id)
        self.assertEqual("foo", n.title)
        self.assertEqual(id, n.id)
        self.assertEqual("This is a summary", n.summary)
        self.assertIsNone(n.vlan)
        self.assertIsNone(n.label)
        self.assertIsNone(n.state)

    def test_setters(self):
        n = network.NetworkResource("foo")
        n.vlan = "bar"
        self.assertEqual("bar", n.attributes["occi.network.vlan"].value)
        n.label = "baz"
        self.assertEqual("baz", n.attributes["occi.network.label"].value)

    def test_getters(self):
        n = network.NetworkResource("foo", vlan="bar", label="baz",
                                    state="foobar")
        self.assertEqual("bar", n.vlan)
        self.assertEqual("baz", n.label)
        self.assertEqual("foobar", n.state)


class TestNetworkMixins(base.TestCase):
    def test_ip_network(self):
        self.assertIsInstance(network.ip_network,
                              mixin.Mixin)
        self.assertEqual("ipnetwork",
                         network.ip_network.term)
        self.assertIn("occi.network.address", network.ip_network.attributes)
        self.assertIn("occi.network.gateway", network.ip_network.attributes)
        self.assertIn("occi.network.allocation", network.ip_network.attributes)

    def test_ip_network_interface(self):
        self.assertIsInstance(network_link.ip_network_interface,
                              mixin.Mixin)
        self.assertEqual("ipnetworkinterface",
                         network_link.ip_network_interface.term)
        self.assertIn("occi.networkinterface.address",
                      network_link.ip_network_interface.attributes)
        self.assertIn("occi.networkinterface.gateway",
                      network_link.ip_network_interface.attributes)
        self.assertIn("occi.networkinterface.allocation",
                      network_link.ip_network_interface.attributes)


class TestOCCINetworkInterface(base.TestCase):
    def test_networkinterface_class(self):
        l = network_link.NetworkInterface
        self.assertIn("occi.core.id", l.attributes)
        self.assertIn("occi.core.title", l.attributes)
        self.assertIn("occi.core.source", l.attributes)
        self.assertIn("occi.core.target", l.attributes)
        self.assertIn("occi.networkinterface.interface", l.attributes)
        self.assertIn("occi.networkinterface.mac", l.attributes)
        self.assertIn("occi.networkinterface.state", l.attributes)
        self.assertIn(link.Link.kind, l.kind.related)
        self.assertEqual(l.kind.location, "networklink/")

    def test_networkinterface(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        n = network.NetworkResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        l = network_link.NetworkInterface([], c, n)
        self.assertEqual(c, l.source)
        self.assertEqual(n, l.target)
        self.assertIsNone(l.interface)
        self.assertIsNone(l.mac)
        self.assertIsNone(l.state)

    def test_setters(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        n = network.NetworkResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        l = network_link.NetworkInterface([], c, n)
        l.mac = "00:00:00:00:00:00"
        self.assertEqual("00:00:00:00:00:00",
                         l.attributes["occi.networkinterface.mac"].value)

    def test_getters(self):
        c = compute.ComputeResource("foo",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        n = network.NetworkResource("bar",
                                    summary="This is a summary",
                                    id=uuid.uuid4().hex)
        l = network_link.NetworkInterface([], c, n, interface="eth1",
                                          mac="00:01:02:03:04:05", state="foo")
        self.assertEqual("eth1", l.interface)
        self.assertEqual("00:01:02:03:04:05", l.mac)
        self.assertEqual("foo", l.state)
