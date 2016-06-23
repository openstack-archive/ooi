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

from ooi.occi.rendering import text
from ooi.tests.unit.occi.renderings import test_header


class TestOCCITextRendering(test_header.TestOCCIHeaderRendering):
    def setUp(self):
        super(TestOCCITextRendering, self).setUp()
        self.renderer = text

    def get_category(self, occi_class, obj, location=None):
        hdrs = super(TestOCCITextRendering,
                     self).get_category(occi_class, obj, location)
        result = []
        for hdr in hdrs:
            result.append("%s: %s" % hdr)
        return "\n".join(result)

    def assertException(self, obj, observed):
        self.assertEqual(obj.explanation, observed)

    def assertLink(self, obj, observed):
        observed_lines = observed.split("\n")
        category = self.get_category("kind", obj.kind,
                                     location=obj.kind.location)
        self.assertIn(category, observed_lines)
        attrs = [
            'occi.core.title="%s"' % obj.title,
            'occi.core.id="%s"' % obj.id,
            'occi.core.target="%s"' % obj.target.location,
            'occi.core.source="%s"' % obj.source.location,
        ]
        for attr in attrs:
            self.assertIn("X-OCCI-Attribute: %s" % attr, observed_lines)

    def assertMixedCollection(self, kind, resource, observed):
        expected = [self.get_category("kind", kind, kind.location)]
        expected.append(self.get_category("kind", resource.kind,
                                          resource.kind.location))
        for a in resource.attributes:
            if resource.attributes[a].value:
                expected.append('X-OCCI-Attribute: '
                                '%s="%s"' % (a, resource.attributes[a].value))
        self.assertEqual("\n".join(expected).strip(), observed.strip())

    def assertCollection(self, obj, observed):
        expected = []
        for what in [obj.kinds, obj.mixins, obj.actions, obj.resources,
                     obj.links]:
            for el in what:
                expected.append("X-OCCI-Location: %s" % el.location)
        self.assertEqual("\n".join(expected).strip(), observed.strip())

    def assertResource(self, obj, observed):
        expected = [self.get_category("kind", obj.kind, obj.kind.location)]
        for a in obj.attributes:
            # assume string attributes
            expected.append('X-OCCI-Attribute: '
                            '%s="%s"' % (a, obj.attributes[a].value))
        self.assertEqual("\n".join(expected), observed)

    def assertResourceMixins(self, obj, mixins, observed):
        observed_lines = observed.split("\n")
        for m in mixins:
            expected = self.get_category("mixin", m)
            self.assertIn(expected, observed_lines)

    def assertResourceActions(self, obj, actions, observed):
        observed_lines = observed.split("\n")
        for a in actions:
            d = {
                'resource': obj.id,
                'location': a.location,
                'rel': a.type_id,
            }
            expected = ('Link: '
                        '<resource/%(resource)s%(location)s>; '
                        'rel="%(rel)s"' % d)
            self.assertIn(expected, observed_lines)

    def assertResourceStringAttr(self, obj, attr, observed):
        expected = 'X-OCCI-Attribute: %s="%s"' % (attr[0], attr[1])
        self.assertIn(expected, observed.split("\n"))

    def assertResourceIntAttr(self, obj, attr, observed):
        expected = 'X-OCCI-Attribute: %s=%s' % (attr[0], attr[1])
        self.assertIn(expected, observed.split("\n"))

    def assertResourceBoolAttr(self, obj, attr, observed):
        v = str(attr[1]).lower()
        expected = 'X-OCCI-Attribute: %s="%s"' % (attr[0], v)
        self.assertIn(expected, observed.split("\n"))

    def assertResourceLink(self, obj1, obj2, observed):
        link = obj1.links[0]
        for line in observed.split("\n"):
            header, content = line.split(":", 1)
            if header == "Link":
                parsed = [f.strip() for f in content.split(";")]
                self.assertEqual(link.location, parsed[0][1:-1])
                rel = 'rel="%s"' % obj2.kind.type_id
                self.assertEqual(rel, parsed[1])
                self_ = 'self="%s"' % link.location
                self.assertEqual(self_, parsed[2])
                source = 'occi.core.source="%s"' % obj1.location
                self.assertIn(source, parsed[3:])
                target = 'occi.core.target="%s"' % obj2.location
                self.assertIn(target, parsed[3:])
                id = 'occi.core.id="%s"' % link.id
                self.assertIn(id, parsed[3:])
                break
        else:
            self.fail("One link was expected")
