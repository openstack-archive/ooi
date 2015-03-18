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

from ooi.tests.middleware import test_middleware


def create_fake_json_resp(data):
    r = webob.Response()
    r.headers["Content-Type"] = "application/json"
    r.charset = "utf8"
    r.body = json.dumps(data).encode("utf8")
    return r


class TestComputeController(test_middleware.TestMiddleware):
    """Test OCCI compute controller."""

    def test_list_vms_empty(self):
        tenant = uuid.uuid4().hex
        d = {"servers": []}
        fake_resp = {
            '/%s/servers' % tenant: create_fake_json_resp(d),
        }
        app = self.get_app(resp=fake_resp)

        req = self._build_req("/compute", method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual("/%s/servers" % tenant, req.environ["PATH_INFO"])

        expected_result = ""
        self.assertContentType(resp)
        self.assertExpectedResult(expected_result, resp)
        self.assertEqual(200, resp.status_code)

    def test_list_vms_one_vm(self):
        tenant = uuid.uuid4().hex

        d = {"servers": [{"id": uuid.uuid4().hex, "name": "foo"},
                         {"id": uuid.uuid4().hex, "name": "bar"},
                         {"id": uuid.uuid4().hex, "name": "baz"}]}

        fake_resp = {
            '/%s/servers' % tenant: create_fake_json_resp(d),
        }

        app = self.get_app(resp=fake_resp)
        req = self._build_req("/compute", method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual("/%s/servers" % tenant, req.environ["PATH_INFO"])

        self.assertEqual(200, resp.status_code)
        expected = []
        for s in d["servers"]:
            expected.append(("X-OCCI-Location", "/compute/%s" % s["id"]))
        self.assertExpectedResult(expected, resp)

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
        app = self.get_app(resp=fake_resp)
        req = self._build_req("/compute/%s" % server_id, method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        expected = [
            ('Category', 'compute; scheme="http://schemas.ogf.org/occi/infrastructure"; class="kind"'),  # noqa
            ('Category', '2; scheme="http://schemas.openstack.org/template/os"; class="mixin"'),  # noqa
            ('Category', 'foo; scheme="http://schemas.openstack.org/template/resource"; class="mixin"'),  # noqa
            ('X-OCCI-Attribute', 'occi.core.title="foo"'),
            ('X-OCCI-Attribute', 'occi.compute.state="active"'),
            ('X-OCCI-Attribute', 'occi.compute.memory=256'),
            ('X-OCCI-Attribute', 'occi.compute.cores=2'),
            ('X-OCCI-Attribute', 'occi.compute.hostname="foo"'),
            ('X-OCCI-Attribute', 'occi.core.id="%s"' % server_id),
        ]
        self.assertContentType(resp)
        self.assertExpectedResult(expected, resp)
        self.assertEqual(200, resp.status_code)

    def test_create_vm(self):
        tenant = uuid.uuid4().hex
        server_id = uuid.uuid4().hex

        s = {"server": {"id": server_id,
                        "name": "foo",
                        "flavor": {"id": "1"},
                        "image": {"id": "2"},
                        "status": "ACTIVE"}}

        fake_resp = {"/%s/servers" % tenant: create_fake_json_resp(s)}
        app = self.get_app(resp=fake_resp)
        headers = {
            'Category': (
                'compute;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind",'
                'big;'
                'scheme="http://schemas.openstack.org/template/resource#";'
                'class="mixin",'
                'cirros;'
                'scheme="http://schemas.openstack.org/template/os#";'
                'class="mixin"')
        }
        req = self._build_req("/compute", method="POST", headers=headers)

        m = mock.MagicMock()
        m.user.project_id = tenant
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        expected = [("X-OCCI-Location", "/compute/%s" % server_id)]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertContentType(resp)


class ComputeControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                 TestComputeController):
    """Test OCCI compute controller with Accept: text/plain."""


class ComputeControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                TestComputeController):
    """Test OCCI compute controller with Accept: text/occi."""
