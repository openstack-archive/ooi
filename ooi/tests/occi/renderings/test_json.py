# -*- coding: utf-8 -*-

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

from ooi.occi.rendering import occi_json
from ooi.tests.occi.renderings import base


class TestOCCIJsonRendering(base.BaseRendererTest):
    def setUp(self):
        super(TestOCCIJsonRendering, self).setUp()
        self.renderer = occi_json

    def get_category(self, occi_class, obj):
        d = {
            "scheme": obj.scheme,
            "term": obj.term,
            "title": obj.title,
            "class": occi_class
        }
        cat = [('Category',
                '%(term)s; scheme="%(scheme)s"; '
                'class="%(class)s"; '
                'title="%(title)s"' % d)]
        return cat

    def assertAction(self, obj, observed):
        expected = self.get_category("action", obj)
        self.assertEqual(expected, observed)

    def assertKind(self, obj, observed):
        expected = {
            "term": obj.term,
            "scheme": obj.scheme,
            "title": obj.title
        }
        self.assertEqual(expected, json.loads(observed))

    def assertResource(self, obj, observed):
        # print observed
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
        observed = json.loads(observed)
        expected = {attr[0]: attr[1]}
        self.assertEqual(expected, observed['attributes'])

    def assertResourceStringAttr(self, obj, attr, observed):
        self.assertResourceAttr(obj, attr, observed)

    def assertResourceIntAttr(self, obj, attr, observed):
        self.assertResourceAttr(obj, attr, observed)

    def assertResourceBoolAttr(self, obj, attr, observed):
        self.assertResourceAttr(obj, attr, observed)

    def assertResourceLink(self, obj1, obj2, observed):
        observed = json.loads(observed)
        link = {
            "kind": obj1.links[0].kind.type_id,
            "id": obj1.links[0].id,
            "source": {
                "location": obj1.location,
                "kind": obj1.kind.type_id
            },
            "target": {
                "location": obj2.location,
                "kind": obj2.kind.type_id,
            },
            "title": obj1.links[0].title,
        }
        self.assertEqual(link, observed["links"][0])

    def assertException(self, obj, observed):
        expected = [('X-OCCI-Error', obj.explanation)]
        self.assertEqual(expected, observed)
