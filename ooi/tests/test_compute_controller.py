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


class TestComputeMiddleware(base.TestCase):
    def setUp(self):
        super(TestComputeMiddleware, self).setUp()

        self.app = wsgi.OCCIMiddleware(fake_app)

    def test_list_vms_all(self):
        req = webob.Request.blank("/compute",
                                  method="GET")
        req.environ["keystone.token_info"] = {
            "token": {
                "tenant": {"id": "3dd7b3f6-c19d-11e4-8dfc-aa07a5b093db"}}}

        req.get_response(self.app)

        self.assertEqual("/v2/3dd7b3f6-c19d-11e4-8dfc-aa07a5b093db/servers",
                         req.environ["PATH_INFO"])
