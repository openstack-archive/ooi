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
import uuid

import mock
import webob
import webob.dec
import webob.exc

from ooi.tests import base
from ooi import wsgi


def fake_app(resp):
    @webob.dec.wsgify
    def app(req):
        return resp
    return app


def create_fake_json_resp(data):
    r = webob.Response()
    r.headers["Content-Type"] = "application/json"
    r.charset = "utf8"
    r.body = json.dumps(data).encode("utf8")
    return r


class TestComputeMiddleware(base.TestCase):
    def test_list_vms_empty(self):
        d = {"servers": []}
        fake_resp = create_fake_json_resp(d)

        app = wsgi.OCCIMiddleware(fake_app(fake_resp))
        req = webob.Request.blank("/compute", method="GET")

        m = mock.MagicMock()
        m.user.project_id = "3dd7b3f6-c19d-11e4-8dfc-aa07a5b093db"
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual("/3dd7b3f6-c19d-11e4-8dfc-aa07a5b093db/servers",
                         req.environ["PATH_INFO"])

        self.assertEqual(200, resp.status_code)
        self.assertEqual("", resp.text)

    def test_list_vms_one_vm(self):
        tenant = uuid.uuid4().hex

        d = {"servers": [{"id": uuid.uuid4().hex, "name": "foo"},
                         {"id": uuid.uuid4().hex, "name": "bar"},
                         {"id": uuid.uuid4().hex, "name": "baz"}]}

        fake_resp = create_fake_json_resp(d)

        app = wsgi.OCCIMiddleware(fake_app(fake_resp))
        req = webob.Request.blank("/compute", method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual("/%s/servers" % tenant, req.environ["PATH_INFO"])

        self.assertEqual(200, resp.status_code)
        for s in d["servers"]:
            expected = "X-OCCI-Location: /compute/%s" % s["id"]
            self.assertIn(expected, resp.text)
