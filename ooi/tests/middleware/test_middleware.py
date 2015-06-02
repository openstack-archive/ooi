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

import mock
import webob
import webob.dec
import webob.exc

from ooi.tests import base
from ooi.tests import fakes
from ooi import wsgi


class TestMiddleware(base.TestCase):
    """OCCI middleware test without Accept header.

    According to the OCCI HTTP rendering, no Accept header
    means text/plain.
    """

    def setUp(self):
        super(TestMiddleware, self).setUp()

        self.accept = self.content_type = None
        self.application_url = fakes.application_url

        self.occi_string = "OCCI/1.1"

    def get_app(self, resp=None):
        return wsgi.OCCIMiddleware(fakes.FakeApp())

    def assertDefaults(self, result):
        self.assertContentType(result)
        self.assertServerHeader(result)

    def assertContentType(self, result):
        if self.accept in (None, "*/*"):
            expected = "text/plain"
        else:
            expected = self.accept
        self.assertEqual(expected, result.content_type)

    def assertServerHeader(self, result):
        self.assertIn("Server", result.headers)
        self.assertIn(self.occi_string, result.headers["server"])

    def assertExpectedResult(self, expected, result):
        expected = ["%s: %s" % e for e in expected]
        # NOTE(aloga): the order of the result does not matter
        results = result.text.splitlines()
        self.assertItemsEqual(expected, results)

    def assertResultIncludesLink(self, link_id, source, target, result):
        expected_attrs = set([
            'occi.core.source="%s"' % source,
            'occi.core.target="%s"' % target,
            'occi.core.id="%s"' % link_id,
        ])
        for lines in result.text.splitlines():
            r = lines.split(":", 1)
            if r[0] == "Link":
                attrs = set([s.strip() for s in r[1].split(";")])
                if expected_attrs.issubset(attrs):
                    return
        self.fail("Failed to find %s in %s." % (expected_attrs, result))

    def _build_req(self, path, tenant_id, **kwargs):
        if self.accept is not None:
            kwargs["accept"] = self.accept

        if self.content_type is not None:
            kwargs["content_type"] = self.content_type

        m = mock.MagicMock()
        m.user.project_id = tenant_id
        environ = {"keystone.token_auth": m}

        kwargs["base_url"] = self.application_url

        return webob.Request.blank(path, environ=environ, **kwargs)

    def test_404(self):
        result = self._build_req("/", "tenant").get_response(self.get_app())
        self.assertEqual(404, result.status_code)
        self.assertDefaults(result)

    def test_good_user_agent(self):
        req = self._build_req("/", "tenant")
        req.user_agent = "foo OCCI/1.1 bar"
        result = req.get_response(self.get_app())
        self.assertEqual(404, result.status_code)
        self.assertDefaults(result)

    def test_bad_user_agent(self):
        req = self._build_req("/", "tenant")
        req.user_agent = "foo OCCI/2.2 bar"
        result = req.get_response(self.get_app())
        self.assertEqual(501, result.status_code)
        self.assertDefaults(result)

    def test_ugly_user_agent(self):
        req = self._build_req("/", "tenant")
        req.user_agent = "fooOCCI/1.1bar"
        result = req.get_response(self.get_app())
        self.assertEqual(404, result.status_code)
        self.assertDefaults(result)

    def test_400_from_openstack(self):
        @webob.dec.wsgify()
        def _fake_app(req):
            exc = webob.exc.HTTPBadRequest()
            resp = fakes.FakeOpenStackFault(exc)
            return resp

        mdl = wsgi.OCCIMiddleware(_fake_app)
        result = self._build_req("/-/", "tenant").get_response(mdl)
        self.assertEqual(400, result.status_code)
        self.assertDefaults(result)


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

    def assertResultIncludesLink(self, link_id, source, target, result):
        expected_attrs = set([
            'occi.core.source="%s"' % source,
            'occi.core.target="%s"' % target,
            'occi.core.id="%s"' % link_id,
        ])
        for val in result.headers.getall("Link"):
            attrs = set([s.strip() for s in val.split(";")])
            if expected_attrs.issubset(attrs):
                return
        self.fail("Failed to find %s in %s." % (expected_attrs, result))
