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

from ooi.occi.core import resource
from ooi.occi.infrastructure import compute
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
