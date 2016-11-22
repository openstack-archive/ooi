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

import collections


from ooi import exception
from ooi.tests import base
from ooi.wsgi import parsers


class BaseParserTest(object):
    """Base class for the parser tests."""

    def test_kind(self):
        h, b = self.get_test_kind({
            "term": "foo",
            "scheme": "http://example.com/scheme#"
        })
        parser = self._get_parser(h, b)
        res = parser.parse()
        self.assertEqual("http://example.com/scheme#foo", res["category"])
        self.assertItemsEqual(["foo"],
                              res["schemes"]["http://example.com/scheme#"])
        self.assertEqual({}, res["mixins"])
        self.assertEqual({}, res["attributes"])

    def test_missing_category(self):
        parser = self._get_parser({}, None)
        self.assertRaises(exception.OCCIInvalidSchema,
                          parser.parse)

    def test_mixins(self):
        h, b = self.get_test_mixins(
            {"term": "foo", "scheme": "http://example.com/scheme#"},
            [
                {"term": "bar", "scheme": "http://example.com/scheme#"},
                {"term": "baz", "scheme": "http://example.com/scheme#"},
            ]
        )
        parser = self._get_parser(h, b)
        res = parser.parse()
        expected_mixins = collections.Counter(
            ["http://example.com/scheme#bar", "http://example.com/scheme#baz"])
        expected_terms = ["bar", "baz", "foo"]
        self.assertEqual(expected_mixins, res["mixins"])
        self.assertItemsEqual(expected_terms,
                              res["schemes"]["http://example.com/scheme#"])
        self.assertEqual({}, res["attributes"])

    def test_attributes(self):
        h, b = self.get_test_attributes(
            {"term": "foo", "scheme": "http://example.com/scheme#"},
            [("foo", '"bar"'), ("baz", 1234), ("bazonk", '"foo=123"')]
        )
        parser = self._get_parser(h, b)
        res = parser.parse()
        expected_attrs = {"foo": "bar", "baz": "1234", "bazonk": "foo=123"}
        self.assertEqual(expected_attrs, res["attributes"])

    def test_link(self):
        h, b = self.get_test_link(
            {"term": "foo", "scheme": "http://example.com/scheme#"},
            {
                "id": "bar",
                "attributes": [("foo", "bar"), ("bazonk", '"foo=123"')]
            }
        )
        parser = self._get_parser(h, b)
        res = parser.parse()
        expected_links = {"bar": {"foo": "bar", "bazonk": "foo=123"}}
        self.assertEqual(expected_links, res["links"])


class TestHeaderParser(BaseParserTest, base.TestCase):
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

    def get_test_attributes(self, kind, attributes):
        h, b = self.get_test_kind(kind)
        attrs = ["%s=%s" % (a[0], a[1]) for a in attributes]
        h["X-OCCI-Attribute"] = ", ".join(attrs)
        return h, b

    def get_test_link(self, kind, link):
        h, b = self.get_test_kind(kind)
        l = ["<%(id)s>" % link]
        for a in link["attributes"]:
            l.append('"%s"=%s' % (a[0], a[1]))
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


class TestTextParser(TestHeaderParser):
    def _get_parser(self, headers, body):
        new_body = [': '.join([hdr, headers[hdr]]) for hdr in headers]
        return parsers.TextParser({}, '\n'.join(new_body))
