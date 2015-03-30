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

from ooi.occi.infrastructure import templates as occi_templates
from ooi.openstack import helpers
from ooi.openstack import mixins
from ooi.openstack import templates
from ooi.tests import base


class TestOpenStackOSTemplate(base.TestCase):
    def test_os_template(self):
        id = uuid.uuid4().hex
        title = "Frobble Image"

        tpl = templates.OpenStackOSTemplate(id,
                                            title)
        self.assertEqual(id, tpl.term)
        self.assertEqual(title, tpl.title)
        self.assertTrue(tpl.scheme.startswith(helpers._PREFIX))
        self.assertIn(occi_templates.os_tpl, tpl.related)


class TestOpenStackResourceTemplate(base.TestCase):
    def test_resource_template(self):
        name = "m1.humongous"
        cores = 10
        memory = 30
        disk = 40
        swap = 20
        ephemeral = 50

        tpl = templates.OpenStackResourceTemplate(name,
                                                  cores,
                                                  memory,
                                                  disk,
                                                  swap=swap,
                                                  ephemeral=ephemeral)

        self.assertEqual(name, tpl.term)
        self.assertEqual("Flavor: %s" % name, tpl.title)
        self.assertTrue(tpl.scheme.startswith(helpers._PREFIX))
        self.assertIn(occi_templates.resource_tpl, tpl.related)
        self.assertEqual(cores, tpl.cores)
        self.assertEqual(memory, tpl.memory)
        self.assertEqual(disk, tpl.disk)
        self.assertEqual(swap, tpl.swap)
        self.assertEqual(ephemeral, tpl.ephemeral)


class TestHelpers(base.TestCase):
    def test_occi_state(self):
        self.assertEqual("active", helpers.occi_state("ACTIVE"))
        self.assertEqual("suspended", helpers.occi_state("PAUSED"))
        self.assertEqual("suspended", helpers.occi_state("SUSPENDED"))
        self.assertEqual("suspended", helpers.occi_state("STOPPED"))
        self.assertEqual("inactive", helpers.occi_state("BUILDING"))


class TestOpenStackUserData(base.TestCase):
    def test_os_userdata(self):
        user_data = "foobar"

        mxn = mixins.OpenStackUserData(user_data)

        self.assertEqual("user_data", mxn.term)
        self.assertTrue(mxn.scheme.startswith(helpers._PREFIX))
        self.assertEqual(user_data, mxn.user_data)


class TestOpenStackPublicKey(base.TestCase):
    def test_os_userdata(self):
        key_name = "foobar"
        key_data = "1234"

        mxn = mixins.OpenStackPublicKey(key_name, key_data)

        self.assertEqual("public_key", mxn.term)
        self.assertTrue(mxn.scheme.startswith(helpers._PREFIX))
        self.assertEqual(key_name, mxn.name)
        self.assertEqual(key_data, mxn.data)
