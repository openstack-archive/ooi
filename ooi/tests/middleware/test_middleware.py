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
from ooi import wsgi


class TestMiddleware(base.TestCase):
    """OCCI middleware test without Accept header.

    According to the OCCI HTTP rendering, no Accept header
    means text/plain.
    """

    def setUp(self):
        super(TestMiddleware, self).setUp()

        self.accept = None

    def get_app(self, resp=None):
        if resp is None:
            resp = webob.Response()

        @webob.dec.wsgify
        def app(req):
            # FIXME(aloga): raise some exception here
            return resp.get(req.path_info)
        return wsgi.OCCIMiddleware(app)

    def assertContentType(self, result):
        expected = self.accept or "text/plain"
        self.assertEqual(expected, result.content_type)

    def assertExpectedResult(self, expected, result):
        expected = ["%s: %s" % e for e in expected]
        # NOTE(aloga): the order of the result does not matter
        results = result.text.splitlines()
        results.sort()
        expected.sort()
        self.assertEqual(expected, results)

    def _build_req(self, path, **kwargs):
        if self.accept is not None:
            kwargs["accept"] = self.accept
        return webob.Request.blank(path,
                                   **kwargs)

    def test_404(self):
        result = self._build_req("/").get_response(self.get_app())
        self.assertEqual(404, result.status_code)


class TestMiddlewareTextPlain(TestMiddleware):
    """OCCI middleware test with Accept: text/plain."""

    def setUp(self):
        super(TestMiddlewareTextPlain, self).setUp()

        self.accept = "text/plain"

    def test_correct_accept(self):
        self.assertEqual("text/plain", self.accept)


class TestMiddlewareTextOcci(TestMiddleware):
    """OCCI middleware text with Accept: text/occi."""

    def setUp(self):
        super(TestMiddlewareTextOcci, self).setUp()

        self.accept = "text/occi"

    def assertExpectedResult(self, expected, result):
        for hdr, val in expected:
            self.assertIn(val, result.headers.getall(hdr))

    def test_correct_accept(self):
        self.assertEqual("text/occi", self.accept)
