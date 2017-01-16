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

from ooi.occi.rendering import headers
from ooi.tests.unit.occi.renderings import base


class TestOCCIHeaderRendering(base.BaseRendererTest):
    def setUp(self):
        super(TestOCCIHeaderRendering, self).setUp()
        self.renderer = headers

    def get_category(self, occi_class, obj, location=None):
        d = {
            "scheme": obj.scheme,
            "term": obj.term,
            "title": obj.title,
            "class": occi_class
        }
        r = ('%(term)s; scheme="%(scheme)s"; '
             'class="%(class)s"; '
             'title="%(title)s"' % d)
        rel = getattr(obj, "parent", None)
        if rel:
            r += '; rel="%s"' % rel.type_id
        if location:
            r += '; location="%s"' % location
        cat = [('Category', r)]
        return cat

    def assertAction(self, obj, observed):
        expected = self.get_category("action", obj)
        self.assertEqual(expected, observed)

    def assertCollection(self, obj, observed):
        expected = []
        for what in [obj.kinds, obj.mixins, obj.actions, obj.resources,
                     obj.links]:
            for el in what:
                expected.append(('X-OCCI-Location', el.location))
        self.assertEqual(expected, observed)

    def assertException(self, obj, observed):
        expected = [('X-OCCI-Error', obj.explanation)]
        self.assertEqual(expected, observed)

    def assertKind(self, obj, observed):
        expected = self.get_category("kind", obj)
        self.assertEqual(expected, observed)

    def assertKindAttr(self, obj, attr, observed):
        self.skipTest("Kind attribute rendering missing for headers")

    def assertLink(self, obj, observed):
        category = self.get_category("kind", obj.kind,
                                     location=obj.kind.location)
        self.assertIn(category.pop(), observed)
        attrs = [
            'occi.core.title="%s"' % obj.title,
            'occi.core.id="%s"' % obj.id,
            'occi.core.target="%s"' % obj.target.location,
            'occi.core.source="%s"' % obj.source.location,
        ]
        for attr in attrs:
            self.assertIn(("X-OCCI-Attribute", attr), observed)

    def assertMixedCollection(self, kind, resource, observed):
        expected = self.get_category("kind", kind, kind.location)
        expected.extend(self.get_category("kind", resource.kind,
                                          resource.kind.location))
        for a in resource.attributes:
            # assume string attributes, remove null ones
            if resource.attributes[a].value:
                attr = ('X-OCCI-Attribute',
                        '%s="%s"' % (a, resource.attributes[a].value))
                expected.append(attr)
        self.assertItemsEqual(expected, observed)

    def assertMixin(self, obj, observed):
        expected = self.get_category("mixin", obj)
        self.assertEqual(expected, observed)

    def assertResource(self, obj, observed):
        expected = self.get_category("kind", obj.kind, obj.kind.location)
        for a in obj.attributes:
            # assume string attributes
            expected.append(('X-OCCI-Attribute',
                             '%s="%s"' % (a, obj.attributes[a].value)))
        self.assertEqual(expected, observed)

    def assertResourceMixins(self, obj, mixins, observed):
        for m in mixins:
            expected = self.get_category("mixin", m).pop()
            self.assertIn(expected, observed)

    def assertResourceActions(self, obj, actions, observed):
        for a in actions:
            d = {
                'resource': obj.id,
                'location': a.location,
                'rel': a.type_id,
            }
            expected = ('Link',
                        '<resource/%(resource)s%(location)s>; '
                        'rel="%(rel)s"' % d)
            self.assertIn(expected, observed)

    def assertResourceStringAttr(self, obj, attr, observed):
        expected = ('X-OCCI-Attribute', '%s="%s"' % (attr[0], attr[1]))
        self.assertIn(expected, observed)

    def assertResourceIntAttr(self, obj, attr, observed):
        expected = ('X-OCCI-Attribute', '%s=%s' % (attr[0], attr[1]))
        self.assertIn(expected, observed)

    def assertResourceBoolAttr(self, obj, attr, observed):
        v = str(attr[1]).lower()
        expected = ('X-OCCI-Attribute', '%s="%s"' % (attr[0], v))
        self.assertIn(expected, observed)

    def assertResourceLink(self, obj1, obj2, observed):
        link = obj1.links[0]
        for h in observed:
            if h[0] == "Link":
                parsed = [f.strip() for f in h[1].split(";")]
                self.assertEqual(link.location, parsed[0][1:-1])
                rel = 'rel="%s"' % obj2.kind.type_id
                self.assertEqual(rel, parsed[1])
                self_ = 'self="%s"' % link.location
                self.assertEqual(self_, parsed[2])
                expected_cats = [link.kind.type_id]
                expected_cats.extend([m.type_id for m in link.mixins])
                category_field = parsed[3].split('=')
                self.assertEqual('category', category_field[0])
                link_cats = category_field[1][1:-1].split()
                self.assertItemsEqual(expected_cats, link_cats)
                source = 'occi.core.source="%s"' % obj1.location
                self.assertIn(source, parsed[4:])
                target = 'occi.core.target="%s"' % obj2.location
                self.assertIn(target, parsed[4:])
                id = 'occi.core.id="%s"' % link.id
                self.assertIn(id, parsed[4:])
                break
        else:
            self.fail("One link was expected")
