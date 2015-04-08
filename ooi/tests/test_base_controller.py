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

import json

import webob
import webob.exc

import ooi.api.base
from ooi.tests import base
from ooi import utils


class TestController(base.TestCase):
    def test_controller(self):
        class Foo(object):
            pass
        controller = ooi.api.base.Controller(Foo(), "version")
        self.assertIsInstance(controller.app, Foo)
        self.assertEqual("version", controller.openstack_version)

    def test_new_request(self):
        controller = ooi.api.base.Controller(None, "version")
        req = webob.Request.blank("foo")
        new_req = controller._get_req(req)
        self.assertEqual("version", new_req.script_name)
        self.assertEqual("foo", new_req.path_info)
        self.assertIsNot(req, new_req)

    def test_new_request_with_path(self):
        controller = ooi.api.base.Controller(None, "version")
        req = webob.Request.blank("foo")
        new_req = controller._get_req(req, path="bar")
        self.assertEqual("bar", new_req.path_info)

    def test_new_request_with_body(self):
        controller = ooi.api.base.Controller(None, "version")
        req = webob.Request.blank("foo")
        new_req = controller._get_req(req, body="bar")
        self.assertEqual(utils.utf8("bar"), new_req.body)

    def test_new_request_with_content_type(self):
        controller = ooi.api.base.Controller(None, "version")
        req = webob.Request.blank("foo")
        new_req = controller._get_req(req, content_type="foo/bar")
        self.assertEqual("foo/bar", new_req.content_type)

    def test_get_from_response(self):
        d = {"element": {"foo": "bar"}}
        body = json.dumps(d)
        response = webob.Response(status=200, body=body)
        result = ooi.api.base.Controller.get_from_response(response,
                                                           "element",
                                                           {})
        self.assertEqual(d["element"], result)

    def test_get_from_response_with_default(self):
        d = {"element": {"foo": "bar"}}
        body = json.dumps({})
        response = webob.Response(status=200, body=body)
        result = ooi.api.base.Controller.get_from_response(response,
                                                           "element",
                                                           d["element"])
        self.assertEqual(d["element"], result)

    def test_get_from_response_with_exception(self):
        d = {"unauthorized": {"message": "unauthorized"}}
        body = json.dumps(d)
        response = webob.Response(status=403, body=body)
        self.assertRaises(webob.exc.HTTPForbidden,
                          ooi.api.base.Controller.get_from_response,
                          response,
                          "foo",
                          {})
