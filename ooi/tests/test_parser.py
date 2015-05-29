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


class TestParserBase(base.TestCase):
    """Base parser tests, uses the header Parser."""

    def _get_parser(self, headers, body):
        return parsers.HeaderParser(headers, body)

    def test_kind(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind"')
        }
        parser = self._get_parser(headers, None)
        res = parser.parse()
        self.assertEqual("http://example.com/scheme#foo", res["category"])
        self.assertItemsEqual(["foo"],
                              res["schemes"]["http://example.com/scheme#"])
        self.assertEqual({}, res["mixins"])
        self.assertEqual({}, res["attributes"])

    def test_missing_categories(self):
        parser = self._get_parser({}, None)
        self.assertRaises(exception.OCCIInvalidSchema,
                          parser.parse)

    def test_bad_category(self):
        headers = {
            'Category': 'foo; scheme;'
        }
        parser = self._get_parser(headers, None)
        self.assertRaises(exception.OCCIInvalidSchema,
                          parser.parse)

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

    def test_mixins(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind", '
                         'bar; '
                         'scheme="http://example.com/scheme#"; '
                         'class="mixin", '
                         'baz; '
                         'scheme="http://example.com/scheme#"; '
                         'class="mixin"')
        }
        parser = self._get_parser(headers, None)
        res = parser.parse()
        expected_mixins = collections.Counter(
            ["http://example.com/scheme#bar", "http://example.com/scheme#baz"])
        expected_terms = ["bar", "baz", "foo"]
        self.assertEqual(expected_mixins, res["mixins"])
        self.assertItemsEqual(expected_terms,
                              res["schemes"]["http://example.com/scheme#"])
        self.assertEqual({}, res["attributes"])

    def test_attributes(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind"'),
            'X-OCCI-Attribute': 'foo="bar", baz=1234, bazonk="foo=123"',
        }
        parser = self._get_parser(headers, None)
        res = parser.parse()
        expected_attrs = {"foo": "bar", "baz": "1234", "bazonk": "foo=123"}
        self.assertEqual(expected_attrs, res["attributes"])


class TestTextParser(TestParserBase):
    def _get_parser(self, headers, body):
        new_body = [': '.join([hdr, headers[hdr]]) for hdr in headers]
        return parsers.TextParser({}, '\n'.join(new_body))
