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

from ooi.tests.parsers import base
from ooi.wsgi import parsers


class TestJsonParser(base.BaseParserTest):
    def _get_parser(self, headers, body):
        return parsers.JsonParser(headers, body)

    def _get_kind(self, kind):
        return '"kind": "%(scheme)s%(term)s"' % kind

    def get_test_kind(self, kind):
        body = "{ %s }" % self._get_kind(kind)
        return {}, body

    def get_test_mixins(self, kind, mixins):
        body = [self._get_kind(kind)]
        body.append('"mixins": [ %s ]'
                    % ','.join(['"%(scheme)s%(term)s"' % m for m in mixins]))
        return {}, "{ %s }" % ",".join(body)

    def _get_attribute_value(self, value):
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, numbers.Number):
            return "%s" % value
        else:
            return '"%s"' % value

    def get_test_attributes(self, kind, attributes):
        body = [self._get_kind(kind)]
        attrs = []
        for n, v in attributes.items():
            attrs.append('"%s": %s' % (n, self._get_attribute_value(v)))
        body.append('"attributes": { %s }' % ",".join(attrs))
        return {}, "{ %s }" % ",".join(body)

    def get_test_link(self, kind, link):
        body = [self._get_kind(kind)]
        attrs = []
        for n, v in link["attributes"].items():
            attrs.append('"%s": %s' % (n, self._get_attribute_value(v)))
        target = '"location": "%(target)s", "kind": "%(kind)s"' % link
        l = ('"links": [{"attributes": { %s }, "target": { %s }, "id": "%s" }]'
             % (",".join(attrs), target, link["id"]))
        body.append(l)
        return {}, "{ %s }" % ",".join(body)
