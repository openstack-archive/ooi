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


import numbers

from ooi import exception
from ooi.tests.parsers import base
from ooi.wsgi import parsers


class TestHeaderParser(base.BaseParserTest):
    """Tests for the Header Parser."""

    def _get_parser(self, headers, body):
        return parsers.HeaderParser(headers, body)

    def get_test_kind(self, kind):
        headers = {
            "Category": ('%(term)s; scheme="%(scheme)s"; class="kind"') % kind,
        }
        return headers, None

    def get_test_mixins(self, kind, mixins):
        h, b = self.get_test_kind(kind)
        c = [h["Category"]]
        for m in mixins:
            c.append('%(term)s; scheme="%(scheme)s"; class="mixin"' % m)
        h["Category"] = ",".join(c)
        return h, b

    def _get_attribute_value(self, value):
        if isinstance(value, bool):
            return '"%s"' % str(value).lower()
        elif isinstance(value, numbers.Number):
            return "%s" % value
        else:
            return '"%s"' % value

    def get_test_attributes(self, kind, attributes):
        h, b = self.get_test_kind(kind)
        attrs = []
        for n, v in attributes.items():
            attrs.append("%s=%s" % (n, self._get_attribute_value(v)))
        h["X-OCCI-Attribute"] = ", ".join(attrs)
        return h, b

    def get_test_link(self, kind, link):
        h, b = self.get_test_kind(kind)
        l = ["<%(id)s>" % link]
        for n, v in link["attributes"].items():
            l.append('"%s"=%s' % (n, self._get_attribute_value(v)))
        h["Link"] = "; ".join(l)
        return h, b

    def test_multiple_kinds(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind", '
                         'bar; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind"')
        }
        parser = self._get_parser(headers, None)
        self.assertRaises(exception.OCCIInvalidSchema,
                          parser.parse)

    def test_invalid_link(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind"'),
            'Link': ('bar; foo="bar"; "bazonk"="foo=123"')
        }
        parser = self._get_parser(headers, None)
        self.assertRaises(exception.OCCIInvalidSchema,
                          parser.parse)

    def test_bad_category(self):
        headers = {
            'Category': 'foo; scheme;'
        }
        parser = self._get_parser(headers, None)
        self.assertRaises(exception.OCCIInvalidSchema,
                          parser.parse)
