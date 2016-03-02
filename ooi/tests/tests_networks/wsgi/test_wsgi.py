# -*- coding: utf-8 -*-

# Copyright 2015 LIP
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

from occinet import wsgi
from ooi.tests import base
from ooi.wsgi.networks.middleware import OCCINetworkMiddleware, ResourceNet


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

    def show(self, req, id, parameters):
        # Returning a ResponseObject should stop the pipepline
        # so the application won't be called.
        resp = wsgi.ResponseObject([])
        return resp


class FakeMiddleware(OCCINetworkMiddleware):
    def _setup_routes(self):
        self.resources["foo"] = ResourceNet(FakeController())
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
        headers = {
            "Content-Type": "text/occi",
            'Category': 'network; scheme="http://schema/resource#";class="kind",' +
            'subnet11; scheme="http://schema/mixin#";class="mixin", ' +
            'subnet33; scheme="http://schema/mixin#";class="mixin";',
        }
        result = webob.Request.blank("/foos/id890234",
                                     method="GET", headers=headers).get_response(self.app)
        self.assertEqual(204, result.status_code)
        self.assertEqual("", result.text)

    def test_show_no_mixin(self):
        headers = {
            "Content-Type": "text/occi",
            'Category': 'network; scheme="http://schema/resource#";class="kind"'
        }
        result = webob.Request.blank("/foos/id890234",
                                     method="GET", headers=headers).get_response(self.app)
        self.assertEqual(204, result.status_code)
        self.assertEqual("", result.text)

    def test_show_attr(self):
        headers = {
            "Content-Type": "text/occi",
            'X-OCCI-Attribute': 'tenant_id=t1, network_id=n1',
            'Category': 'network; scheme="http://schema/resource#";class="kind"'
        }
        result = webob.Request.blank("/foos/id890234",
                                     method="GET", headers=headers).get_response(self.app)
        self.assertEqual(204, result.status_code)
        self.assertEqual("", result.text)
