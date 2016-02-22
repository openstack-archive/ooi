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

from ooi.occi.rendering import text
from ooi.tests.occi.renderings import test_header


class TestOCCITextRendering(test_header.TestOCCIHeaderRendering):
    def setUp(self):
        super(TestOCCITextRendering, self).setUp()
        self.renderer = text

    def get_category(self, occi_class, obj):
        hdrs = super(TestOCCITextRendering, self).get_category(occi_class, obj)
        result = []
        for hdr in hdrs:
            result.append("%s: %s" % hdr)
        return "\n".join(result)

    def assertException(self, obj, observed):
        self.assertEqual(obj.explanation, observed)
