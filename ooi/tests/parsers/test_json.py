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


from ooi.tests.parsers import base
from ooi.wsgi import parsers


class TestJsonParser(base.BaseParserTest):
    def _get_parser(self, headers, body):
        return parsers.JsonParser(headers, body)

    def get_test_kind(self):
        body = """
            {
                "kind": "http://example.com/scheme#foo"
            }
        """
        return {}, body

    def get_test_mixins(self):
        body = """
            {
                "kind": "http://example.com/scheme#foo",
                "mixins": [
                    "http://example.com/scheme#bar",
                    "http://example.com/scheme#baz"
                ]
            }
        """
        return {}, body

    def get_test_attributes(self):
        body = """
            {
                "kind": "http://example.com/scheme#foo",
                "attributes": {
                    "foo": "bar",
                    "baz": 1234,
                    "bazonk": "foo=123"
                }
            }
        """
        return {}, body

    def get_test_link(self):
        body = """
            {
                "kind": "http://example.com/scheme#foo",
                "links": [
                    {
                        "target": {
                            "kind": "unused"
                            "location": "/bar"
                        }
                        "attributes": {
                            "foo": "bar",
                            "bazonk": "foo=123"
                        }
                    }
                ]
            }
        """
        return {}, body
