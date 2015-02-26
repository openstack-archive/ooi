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

from ooi.occi.core import action
from ooi.occi.core import attribute
from ooi.occi.core import category
from ooi.occi.core import entity
from ooi.occi.core import kind
from ooi.occi.core import link
from ooi.occi.core import mixin
from ooi.occi.core import resource
from ooi.tests import base


class TestAttributes(base.TestCase):
    def test_base(self):
        attr = attribute.Attribute("occi.foo.bar", "crap")
        self.assertEqual("crap", attr.value)

    def test_mutable(self):
        attr = attribute.MutableAttribute("occi.foo.bar", "crap")
        attr.value = "bazonk"
        self.assertEqual("bazonk", attr.value)

    def test_inmutable(self):
        attr = attribute.InmutableAttribute("occi.foo.bar", "crap")

        def set_val():
            attr.value = "bazonk"

        self.assertRaises(AttributeError, set_val)


class TestCoreOCCICategory(base.TestCase):
    args = ("scheme", "term", "title")
    obj = category.Category

    def test_obj(self):
        cat = self.obj(*self.args)

        for i in self.args:
            self.assertEqual(i, getattr(cat, i))

    def test_attributes(self):
        attr = attribute.MutableAttribute("occi.foo.bar", "crap")
        cat = self.obj(*self.args, attributes=[attr])
        self.assertEqual({"occi.foo.bar": attr}, cat.attributes)

    def test_attributes_empty(self):
        cat = self.obj(*self.args, attributes=[])
        self.assertEqual({}, cat.attributes)

    def test_attributes_invalid(self):
        self.assertRaises(TypeError,
                          self.obj,
                          *self.args,
                          attributes=None)

    def test_attributes_invalid_list(self):
        self.assertRaises(TypeError,
                          self.obj,
                          *self.args,
                          attributes=[None])


class TestCoreOCCIKind(TestCoreOCCICategory):
    obj = kind.Kind

    def setUp(self):
        super(TestCoreOCCIKind, self).setUp()

    def test_obj(self):
        k = self.obj(*self.args)
        for i in (self.args):
            self.assertEqual(i, getattr(k, i))

    def test_actions(self):
        actions = [action.Action(None, None, None)]
        kind = self.obj(*self.args, actions=actions)

        for i in (self.args):
            self.assertEqual(i, getattr(kind, i))
        self.assertEqual(actions, kind.actions)

    def test_actions_empty(self):
        actions = []
        kind = self.obj(*self.args, actions=actions)

        for i in (self.args):
            self.assertEqual(i, getattr(kind, i))
        self.assertEqual(actions, kind.actions)

    def test_actions_invalid(self):
        actions = None
        self.assertRaises(TypeError,
                          self.obj,
                          *self.args,
                          actions=actions)

    def test_actions_invalid_list(self):
        actions = [None]
        self.assertRaises(TypeError,
                          self.obj,
                          *self.args,
                          actions=actions)

    def test_related(self):
        related = [self.obj(None, None, None)]
        kind = self.obj(*self.args, related=related)

        for i in (self.args):
            self.assertEqual(i, getattr(kind, i))
        self.assertEqual(related, kind.related)

    def test_related_empty(self):
        related = []
        kind = self.obj(*self.args, related=related)

        for i in (self.args):
            self.assertEqual(i, getattr(kind, i))
        self.assertEqual(related, kind.related)

    def test_related_invalid(self):
        related = None
        self.assertRaises(TypeError,
                          self.obj,
                          *self.args,
                          related=related)

    def test_related_invalid_list(self):
        related = [None]
        self.assertRaises(TypeError,
                          self.obj,
                          *self.args,
                          related=related)


class TestCoreOCCIMixin(TestCoreOCCIKind):
    obj = mixin.Mixin


class TestCoreOCCIAction(TestCoreOCCICategory):
    obj = action.Action


class TestCoreOCCIEntity(base.TestCase):
    def test_entity(self):
        e = entity.Entity("foo", "bar", [])
        self.assertIsInstance(e.kind, kind.Kind)
        self.assertIn("occi.core.id", e.attributes)
        self.assertIn("occi.core.title", e.attributes)

        self.assertEqual("foo", e.attributes["occi.core.id"].value)
        self.assertEqual("foo", e.id)
        self.assertIs(e.id, e.attributes["occi.core.id"].value)

        def set_attr():
            e.attributes["occi.core.id"].value = "foo"
        self.assertRaises(AttributeError, set_attr)

        def set_attr_directly():
            e.id = "foo"
        self.assertRaises(AttributeError, set_attr_directly)

        e.title = "baz"
        self.assertEqual("baz", e.attributes["occi.core.title"].value)
        self.assertEqual("baz", e.title)
        self.assertIs(e.title, e.attributes["occi.core.title"].value)

        e.attributes["occi.core.title"].value = "bar"
        self.assertEqual("bar", e.attributes["occi.core.title"].value)
        self.assertEqual("bar", e.title)
        self.assertIs(e.title, e.attributes["occi.core.title"].value)


class TestCoreOCCIResource(base.TestCase):
    def test_resource(self):
        r = resource.Resource("foo", "bar", [], "baz")
        self.assertIsInstance(r.kind, kind.Kind)
        self.assertEqual("resource", r.kind.term)
        self.assertEqual("foo", r.id)
        self.assertEqual("bar", r.title)
        self.assertEqual("baz", r.summary)
        r.summary = "bazonk"
        self.assertEqual("bazonk", r.summary)

    def test_valid_link(self):
        r1 = resource.Resource(None, None, [], None)
        r2 = resource.Resource(None, None, [], None)
        r1.link(r2)
        self.assertIsInstance(r1.links[0], link.Link)
        self.assertIs(r1, r1.links[0].source)
        self.assertIs(r2, r1.links[0].target)

    def test_mixins(self):
        m = mixin.Mixin(None, None, None)
        r = resource.Resource(None, None, [m], [])
        self.assertIsInstance(r.kind, kind.Kind)
        self.assertEqual([m], r.mixins)

    def test_invalid_mixins(self):
        self.assertRaises(TypeError,
                          resource.Resource,
                          None, None, ["foo"], None)


class TestCoreOCCILink(base.TestCase):
    def test_correct_link(self):
        resource_1 = resource.Resource(None, None, [], None)
        resource_2 = resource.Resource(None, None, [], None)
        resource_3 = resource.Resource(None, None, [], None)
        l = link.Link(None, None, [], resource_1, resource_2)
        self.assertIsInstance(l.kind, kind.Kind)
        self.assertEqual("link", l.kind.term)
        self.assertIs(resource_1, l.source)
        self.assertIs(resource_2, l.target)

        self.assertIs(resource_1, l.attributes["occi.core.source"].value)
        self.assertIs(resource_1, l.source)
        self.assertIs(resource_1, l.attributes["occi.core.source"].value)

        self.assertIs(resource_2, l.attributes["occi.core.target"].value)
        self.assertIs(resource_2, l.target)
        self.assertIs(resource_2, l.attributes["occi.core.target"].value)

        l.source = resource_3
        self.assertIs(resource_3, l.attributes["occi.core.source"].value)
        self.assertIs(resource_3, l.source)
        self.assertIs(resource_3, l.attributes["occi.core.source"].value)

        l.target = resource_1
        self.assertIs(resource_1, l.target)
        self.assertIs(resource_1, l.attributes["occi.core.target"].value)
        self.assertIs(resource_1, l.attributes["occi.core.target"].value)
