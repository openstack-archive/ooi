# -*- coding: utf-8 -*-

# Copyright 2015 LIP - Lisbon
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
from ooi.tests.tests_networks import fakes
from ooi import wsgi


class TestMiddleware(base.TestCase):

    def setUp(self):
        super(TestMiddleware, self).setUp()
        self.accept = self.content_type = None
        self.application_url = fakes.application_url
        self.app = wsgi.OCCIMiddleware(None)

    def assertDefaults(self, result):
        self.assertContentType(result)
        # self.assertNetworkHeader(result)
        # fixme(jorgesece): modify when solve problem
        # of process_response() parametrized

    def assertNetworkHeader(self, result):
        self.assertIn("Network", result.headers)
        self.assertIn(self.occi_string, result.headers["network"])

    def assertContentType(self, result):
        if self.accept in (None, "*/*"):
            expected = "text/plain"
        else:
            expected = self.accept
        self.assertEqual(expected, result.content_type)

    def _build_req(self, path, **kwargs):
        if self.accept is not None:
            kwargs["accept"] = self.accept

        if self.content_type is not None:
            kwargs["content_type"] = self.content_type

        environ = {"HTTP_X-Auth-Token": "XXXX"}
        # fixme(jorgesece): network does not use it

        kwargs["base_url"] = self.application_url

        return webob.Request.blank(path, environ=environ, **kwargs)

    # @mock.patch.object(query.Controller,"_resource_tpls")
    # @mock.patch.object(query.Controller,"_os_tpls")
    # @mock.patch.object(query.Controller,"_ip_pools")
    # def test_query(self,m1,m2,m3):
    #     m1.return_value  =  []
    #     m2.return_value  =  []
    #     m3.return_value  =  []
    #     req = self._build_req("/-/")
    #     result = req.get_response(self.app)
    #     self.assertDefaults(result)
    #     self.assertExpectedResult(fakes.fake_query_results(), result)
    #     self.assertEqual(200, result.status_code)
