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

from ooi.occi.rendering import headers
from ooi.tests.occi.renderings import base


class TestOCCIHeaderRendering(base.BaseRendererTest):
    def setUp(self):
        super(TestOCCIHeaderRendering, self).setUp()
        self.renderer = headers

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
        expected = self.get_category("kind", obj)
        self.assertEqual(expected, observed)

    def assertException(self, obj, observed):
        expected = [('X-OCCI-Error', obj.explanation)]
        self.assertEqual(expected, observed)
