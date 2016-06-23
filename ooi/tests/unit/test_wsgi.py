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
import webob.dec
import webob.exc

from ooi.tests import base
from ooi import wsgi


@webob.dec.wsgify
def fake_app(req):
    resp = webob.Response("Foo")
    return resp


class FakeController(object):
    def index(self, *args, **kwargs):
        return None

    def create(self, req, body):
        raise webob.exc.HTTPNotImplemented()

    def delete(self, req, id):
        raise webob.exc.HTTPNotImplemented()

    def show(self, req, id):
        # Returning a ResponseObject should stop the pipepline
        # so the application won't be called.
        resp = wsgi.ResponseObject([])
        return resp


class FakeMiddleware(wsgi.OCCIMiddleware):
    def _setup_routes(self):
        self.resources["foo"] = wsgi.Resource(FakeController())
        self.mapper.resource("foo", "foos",
                             controller=self.resources["foo"])


class TestMiddleware(base.TestCase):
    def setUp(self):
        super(TestMiddleware, self).setUp()

        self.app = FakeMiddleware(fake_app)

    def test_index(self):
        result = webob.Request.blank("/foos",
                                     method="GET").get_response(self.app)
        self.assertEqual(200, result.status_code)
        self.assertEqual("", result.text)

    def test_show(self):
        result = webob.Request.blank("/foos/stop",
                                     method="GET").get_response(self.app)
        self.assertEqual(204, result.status_code)
        self.assertEqual("", result.text)

    def test_post(self):
        result = webob.Request.blank("/foos",
                                     method="POST").get_response(self.app)
        self.assertEqual(501, result.status_code)

    def test_put(self):
        # there's no put option in the FakeController
        result = webob.Request.blank("/foos/1",
                                     method="PUT").get_response(self.app)
        self.assertEqual(404, result.status_code)

    def test_delete(self):
        result = webob.Request.blank("/foos/1",
                                     method="DELETE").get_response(self.app)
        self.assertEqual(501, result.status_code)

    def test_404(self):
        result = webob.Request.blank("/bazonk").get_response(self.app)
        self.assertEqual(404, result.status_code)

    def test_empty_accept(self):
        req = webob.Request.blank("/foos",
                                  method="GET",
                                  accept=None)
        result = req.get_response(self.app)
        self.assertEqual(200, result.status_code)
        self.assertEqual("text/plain", result.content_type)

    def test_accept_all(self):
        req = webob.Request.blank("/foos",
                                  method="GET",
                                  accept="*/*")
        result = req.get_response(self.app)
        self.assertEqual(200, result.status_code)
        self.assertEqual("text/plain", result.content_type)

    def test_bad_accept(self):
        req = webob.Request.blank("/foos",
                                  method="GET",
                                  accept="foo/bazonk")
        result = req.get_response(self.app)
        self.assertEqual(406, result.status_code)

    def test_various_content_type_post(self):
        req = webob.Request.blank("/foos",
                                  method="POST",
                                  content_type="text/occi,text/plain")
        result = req.get_response(self.app)
        self.assertEqual(501, result.status_code)

    def test_various_one_bad_content_type_post(self):
        req = webob.Request.blank("/foos",
                                  method="POST",
                                  content_type="text/bazonk,text/plain")
        result = req.get_response(self.app)
        self.assertEqual(501, result.status_code)

    def test_various_bad_content_types_post(self):
        req = webob.Request.blank("/foos",
                                  method="POST",
                                  content_type="text/bazonk,text/foobar")
        result = req.get_response(self.app)
        self.assertEqual(406, result.status_code)

    def test_bad_content_type_post(self):
        req = webob.Request.blank("/foos",
                                  method="POST",
                                  content_type="foo/bazonk")
        result = req.get_response(self.app)
        self.assertEqual(406, result.status_code)

    def test_bad_content_type_put(self):
        req = webob.Request.blank("/foos",
                                  method="PUT",
                                  content_type="foo/bazonk")
        result = req.get_response(self.app)
        self.assertEqual(404, result.status_code)

    def test_bad_content_type_get(self):
        req = webob.Request.blank("/foos",
                                  method="GET",
                                  content_type="foo/bazonk")
        result = req.get_response(self.app)
        self.assertEqual(200, result.status_code)

    def test_bad_content_type_delete(self):
        req = webob.Request.blank("/foos",
                                  method="DELETE",
                                  content_type="foo/bazonk")
        result = req.get_response(self.app)
        self.assertEqual(404, result.status_code)


class TestOCCIMiddleware(base.TestCase):
    def setUp(self):
        super(TestOCCIMiddleware, self).setUp()

        self.app = wsgi.OCCIMiddleware(fake_app)
