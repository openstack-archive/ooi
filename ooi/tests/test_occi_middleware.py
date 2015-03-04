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

import webob

from ooi.tests import base
import ooi.tests.test_wsgi
from ooi import wsgi

fake_app = ooi.tests.test_wsgi.fake_app


class TestOCCIMiddleware(base.TestCase):
    def setUp(self):
        super(TestOCCIMiddleware, self).setUp()

        self.app = wsgi.OCCIMiddleware(fake_app)

    def test_404(self):
        result = webob.Request.blank("/").get_response(self.app)
        self.assertEqual(404, result.status_code)

    def test_query(self):
        result = webob.Request.blank("/-/").get_response(self.app)
        self.assertEqual(501, result.status_code)
