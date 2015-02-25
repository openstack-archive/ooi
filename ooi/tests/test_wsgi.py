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
    resp = webob.Response("Hi")
    return resp


class FakeController(object):
    def index(self, *args, **kwargs):
        # Return none so that the middleware passes to the app
        return None

    def create(self, req, body):
        raise webob.exc.HTTPNotImplemented()

    def delete(self, req, id):
        raise webob.exc.HTTPNotImplemented()

    def show(self, req, id):
        # Returning a ResponseObject should stop the pipepline
        # so the application won't be called.
        resp = wsgi.ResponseObject("Show and stop")
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
        self.assertEqual("Hi", result.body)

    def test_show(self):
        result = webob.Request.blank("/foos/stop",
                                     method="GET").get_response(self.app)
        self.assertEqual(200, result.status_code)
        self.assertEqual("Show and stop", result.body)

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

    def test_bad_accept(self):
        req = webob.Request.blank("/foos",
                                  method="GET",
                                  accept="foo/bazonk",
                                  content_type="foo/bazonk")
        result = req.get_response(self.app)
        self.assertEqual(400, result.status_code)
