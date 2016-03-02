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

from ooi.tests.middleware import test_middleware as testmi
from ooi.tests.tests_networks import fakes
from ooi.wsgi.networks.middleware import OCCINetworkMiddleware


class TestMiddleware(testmi.TestMiddleware):
    """OCCI middleware test without Accept header.

    According to the OCCI HTTP rendering, no Accept header
    means text/plain.
    """

    def setUp(self):
        super(TestMiddleware, self).setUp()

    def get_app(self, resp=None):
        return OCCINetworkMiddleware(fakes.FakeApp())

    def assertDefaults(self, result):
        self.assertContentType(result)
        #self.assertNetworkHeader(result)
        #fixme(jorgesece): modify when solve problem of process_response() parametrized

    def assertNetworkHeader(self, result):
        self.assertIn("Network", result.headers)
        self.assertIn(self.occi_string, result.headers["network"])

    def _build_req(self, path, tenant_id, **kwargs):
        if self.accept is not None:
            kwargs["accept"] = self.accept

        if self.content_type is not None:
            kwargs["content_type"] = self.content_type

        environ = {"HTTP_X-Auth-Token":"XXXX", "project": tenant_id} #fixme(jorgesece): network does not use it

        kwargs["base_url"] = self.application_url

        return webob.Request.blank(path, environ=environ, **kwargs)

    # def test_query(self):
    #     tenant_id = fakes.tenants["bar"]["id"]
    #     req = self._build_req("/-/", tenant_id)
    #     result = req.get_response(self.get_app())
    #     self.assertDefaults(result)
    #    # self.assertExpectedResult(fakes.fake_query_results(), result)
    #     self.assertEqual(200, result.status_code)