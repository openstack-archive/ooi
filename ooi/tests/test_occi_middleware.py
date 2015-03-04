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

from ooi.occi.infrastructure import compute
from ooi.tests import base
import ooi.tests.test_wsgi
from ooi import wsgi

fake_app = ooi.tests.test_wsgi.fake_app


class TestOCCIMiddleware(base.TestCase):
    def setUp(self):
        super(TestOCCIMiddleware, self).setUp()

        self.app = wsgi.OCCIMiddleware(fake_app)
        self.accept = None

    def assertContentType(self, result):
        expected = self.accept or "text/plain"
        self.assertEqual(expected, result.content_type)

    def assertExpectedResult(self, expected, result):
        for e in expected:
            self.assertIn(str(e), result.text)

    def _build_req(self, path, **kwargs):
        if self.accept is not None:
            kwargs["accept"] = self.accept
        return webob.Request.blank(path,
                                   **kwargs)

    def test_404(self):
        result = self._build_req("/").get_response(self.app)
        self.assertEqual(404, result.status_code)

    def test_query(self):
        result = self._build_req("/-/").get_response(self.app)

        self.assertContentType(result)
        self.assertExpectedResult(compute.ComputeResource.actions, result)
        self.assertEqual(200, result.status_code)


class TestOCCIMiddlewareContentTypeText(TestOCCIMiddleware):
    def setUp(self):
        super(TestOCCIMiddlewareContentTypeText, self).setUp()

        self.app = wsgi.OCCIMiddleware(fake_app)
        self.accept = "text/plain"


class TestOCCIMiddlewareContentTypeOCCIHeaders(TestOCCIMiddleware):
    def setUp(self):
        super(TestOCCIMiddlewareContentTypeOCCIHeaders, self).setUp()

        self.app = wsgi.OCCIMiddleware(fake_app)
        self.accept = "text/occi"

    def assertExpectedResult(self, expected, result):
        for e in expected:
            for hdr, val in e.headers():
                self.assertIn(val, result.headers.getall(hdr))
