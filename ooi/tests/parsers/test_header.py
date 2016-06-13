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


from ooi import exception
from ooi.tests.parsers import base
from ooi.wsgi import parsers


class TestHeaderParser(base.BaseParserTest):
    """Tests for the Header Parser."""

    def _get_parser(self, headers, body):
        return parsers.HeaderParser(headers, body)

    def get_test_kind(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind"')
        }
        return headers, None

    def get_test_mixins(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind",'
                         'bar; '
                         'scheme="http://example.com/scheme#"; '
                         'class="mixin",'
                         'baz; '
                         'scheme="http://example.com/scheme#"; '
                         'class="mixin"')
        }
        return headers, None

    def get_test_attributes(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind"'),
            'X-OCCI-Attribute': 'foo="bar", baz=1234, bazonk="foo=123"',
        }
        return headers, None

    def get_test_link(self):
        headers = {
            'Category': ('foo; '
                         'scheme="http://example.com/scheme#"; '
                         'class="kind"'),
            'Link': ('<bar>; foo="bar"; "bazonk"="foo=123"')
        }
        return headers, None

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
