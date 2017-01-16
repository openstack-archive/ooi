# Copyright 2016 Spanish National Research Council
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

from ooi.occi.core import attribute
from ooi.occi.rendering import occi_json
from ooi.tests.unit.occi.renderings import base


class TestOCCIJsonRendering(base.BaseRendererTest):
    def setUp(self):
        super(TestOCCIJsonRendering, self).setUp()
        self.renderer = occi_json

    def assertAction(self, obj, observed):
        expected = {
            "term": obj.term,
            "scheme": obj.scheme,
            "title": obj.title
        }
        self.assertEqual(expected, json.loads(observed))

    def assertCollection(self, obj, observed):
        observed_json = json.loads(observed)
        for what, fn in [("kinds", self.assertKind),
                         ("mixins", self.assertMixin),
                         ("actions", self.assertAction),
                         ("links", self.assertLink),
                         ("resources", self.assertResource)]:
            objs = getattr(obj, what)
            if objs:
                dumped_objs = [json.dumps(o) for o in observed_json[what]]
                map(fn, objs, dumped_objs)

    def assertException(self, obj, observed):
        expected = {
            "code": obj.status_code,
            "message": obj.explanation,
        }
        self.assertEqual(expected, json.loads(observed))

    def assertKind(self, obj, observed):
        expected = {
            "term": obj.term,
            "scheme": obj.scheme,
            "title": obj.title,
        }
        self.assertEqual(expected, json.loads(observed))

    def assertKindAttr(self, obj, attr, observed):
        expected = {
            "mutable": isinstance(attr, attribute.MutableAttribute),
            "required": attr.required,
            "type": "string",
        }
        if attr.default:
            expected["default"] = attr.default
        if attr.description:
            expected["description"] = attr.description
        k, v = json.loads(observed)["attributes"].popitem()
        self.assertEqual(k, attr.name)
        self.assertEqual(expected, v)

    def assertLink(self, obj, observed):
        link = {
            "kind": obj.kind.type_id,
            "id": obj.id,
            "source": {
                "location": obj.source.location,
                "kind": obj.source.kind.type_id
            },
            "target": {
                "location": obj.target.location,
                "kind": obj.target.kind.type_id,
            },
            "title": obj.title,
        }
        if obj.mixins:
            link["mixins"] = [m.type_id for m in obj.mixins]
        self.assertEqual(link, json.loads(observed))

    def assertMixedCollection(self, kind, resource, observed):
        c = mock.MagicMock()
        c.kinds = [kind]
        c.resources = [resource]
        c.mixins = ()
        c.actions = ()
        c.links = ()
        self.assertCollection(c, observed)

    def assertMixin(self, obj, observed):
        expected = {
            "term": obj.term,
            "scheme": obj.scheme,
            "title": obj.title
        }
        self.assertEqual(expected, json.loads(observed))

    def assertResource(self, obj, observed):
        expected = {}
        for attr in ["summary", "title", "id"]:
            v = getattr(obj, attr, None)
            if v is not None:
                expected[attr] = v
        expected["kind"] = obj.kind.type_id
        if obj.mixins:
            expected["mixins"] = [m.type_id for m in obj.mixins]
        if obj.actions:
            expected["actions"] = [a.type_id for a in obj.actions]
        self.assertEqual(expected, json.loads(observed))

    def assertResourceActions(self, obj, actions, observed):
        self.assertResource(obj, observed)

    def assertResourceMixins(self, obj, mixins, observed):
        self.assertResource(obj, observed)

    def assertResourceAttr(self, obj, attr, observed):
        observed_json = json.loads(observed)
        expected = {attr[0]: attr[1]}
        self.assertEqual(expected, observed_json['attributes'])

    def assertResourceStringAttr(self, obj, attr, observed):
        self.assertResourceAttr(obj, attr, observed)

    def assertResourceIntAttr(self, obj, attr, observed):
        self.assertResourceAttr(obj, attr, observed)

    def assertResourceBoolAttr(self, obj, attr, observed):
        self.assertResourceAttr(obj, attr, observed)

    def assertResourceLink(self, obj1, obj2, observed):
        self.assertLink(obj1.links[0],
                        json.dumps(json.loads(observed)["links"][0]))

    def test_object_attr(self):
        attr = attribute.MutableAttribute("org.example")
        r = self.renderer.get_renderer(attr)
        observed = r.render()
        expected = {
            "org.example": {
                "type": "string", "required": False, "mutable": True,
            }
        }
        self.assertEqual(expected, json.loads(observed))

    def test_list_attr(self):
        attr = attribute.MutableAttribute(
            "org.example", attr_type=attribute.AttributeType.list_type)
        r = self.renderer.get_renderer(attr)
        observed = r.render()
        expected = {
            "org.example": {
                "type": "array", "required": False, "mutable": True,
            }
        }
        self.assertEqual(expected, json.loads(observed))

    def test_hash_attr(self):
        attr = attribute.MutableAttribute(
            "org.example", attr_type=attribute.AttributeType.hash_type)
        r = self.renderer.get_renderer(attr)
        observed = r.render()
        expected = {
            "org.example": {
                "type": "object", "required": False, "mutable": True,
            }
        }
        self.assertEqual(expected, json.loads(observed))

    def test_string_attr(self):
        attr = attribute.MutableAttribute(
            "org.example", attr_type=attribute.AttributeType.string_type)
        r = self.renderer.get_renderer(attr)
        observed = r.render()
        expected = {
            "org.example": {
                "type": "string", "required": False, "mutable": True,
            }
        }
        self.assertEqual(expected, json.loads(observed))

    def test_number_attr(self):
        attr = attribute.MutableAttribute(
            "org.example", attr_type=attribute.AttributeType.number_type)
        r = self.renderer.get_renderer(attr)
        observed = r.render()
        expected = {
            "org.example": {
                "type": "number", "required": False, "mutable": True,
            }
        }
        self.assertEqual(expected, json.loads(observed))

    def test_boolean_attr(self):
        attr = attribute.MutableAttribute(
            "org.example", attr_type=attribute.AttributeType.boolean_type)
        r = self.renderer.get_renderer(attr)
        observed = r.render()
        expected = {
            "org.example": {
                "type": "boolean", "required": False, "mutable": True,
            }
        }
        self.assertEqual(expected, json.loads(observed))
