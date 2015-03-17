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
        return resp[req.path_info]
    return app


def create_fake_json_resp(data):
    r = webob.Response()
    r.headers["Content-Type"] = "application/json"
    r.charset = "utf8"
    r.body = json.dumps(data).encode("utf8")
    return r


# TODO(enolfc): this should check the resulting obects, not the text.
class TestComputeMiddleware(base.TestCase):
    def test_list_vms_empty(self):
        tenant = uuid.uuid4().hex
        d = {"servers": []}
        fake_resp = {
            '/%s/servers' % tenant: create_fake_json_resp(d),
        }

        app = wsgi.OCCIMiddleware(fake_app(fake_resp))
        req = webob.Request.blank("/compute", method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual("/%s/servers" % tenant, req.environ["PATH_INFO"])

        self.assertEqual(200, resp.status_code)
        self.assertEqual("", resp.text)

    def test_list_vms_one_vm(self):
        tenant = uuid.uuid4().hex

        d = {"servers": [{"id": uuid.uuid4().hex, "name": "foo"},
                         {"id": uuid.uuid4().hex, "name": "bar"},
                         {"id": uuid.uuid4().hex, "name": "baz"}]}

        fake_resp = {
            '/%s/servers' % tenant: create_fake_json_resp(d),
        }

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

    def test_show_vm(self):
        tenant = uuid.uuid4().hex
        server_id = uuid.uuid4().hex
        s = {"server": {"id": server_id,
                        "name": "foo",
                        "flavor": {"id": "1"},
                        "image": {"id": "2"},
                        "status": "ACTIVE"}}
        f = {"flavor": {"id": 1,
                        "name": "foo",
                        "vcpus": 2,
                        "ram": 256,
                        "disk": 10}}
        i = {"image": {"id": 2,
                       "name": "bar"}}

        fake_resp = {
            '/%s/servers/%s' % (tenant, server_id): create_fake_json_resp(s),
            '/%s/flavors/1' % tenant: create_fake_json_resp(f),
            '/%s/images/2' % tenant: create_fake_json_resp(i),
        }
        app = wsgi.OCCIMiddleware(fake_app(fake_resp))
        req = webob.Request.blank("/compute/%s" % server_id, method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual(200, resp.status_code)
        expected = 'X-OCCI-Attribute: occi.core.id="%s"' % server_id
        self.assertIn(expected, resp.text)
