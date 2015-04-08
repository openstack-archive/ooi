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

import uuid

import mock

from ooi.tests import fakes
from ooi.tests.middleware import test_middleware


def build_occi_server(server):
    name = server["name"]
    server_id = server["id"]
    flavor_name = fakes.flavors[server["flavor"]["id"]]["name"]
    ram = fakes.flavors[server["flavor"]["id"]]["ram"]
    cores = fakes.flavors[server["flavor"]["id"]]["vcpus"]
    image_id = server["image"]["id"]

    status = server["status"].upper()
    if status in ("ACTIVE",):
        status = "active"
    elif status in ("PAUSED", "SUSPENDED", "STOPPED"):
        status = "suspended"
    else:
        status = "inactive"

    cats = []
    cats.append('compute; '
                'scheme="http://schemas.ogf.org/occi/infrastructure"; '
                'class="kind"'),
    cats.append('%s; '
                'scheme="http://schemas.openstack.org/template/os"; '
                'class="mixin"' % image_id),
    cats.append('%s; '
                'scheme="http://schemas.openstack.org/template/resource"; '
                'class="mixin"' % flavor_name),

    attrs = [
        'occi.core.title="%s"' % name,
        'occi.compute.state="%s"' % status,
        'occi.compute.memory=%s' % ram,
        'occi.compute.cores=%s' % cores,
        'occi.compute.hostname="%s"' % name,
        'occi.core.id="%s"' % server_id,
    ]
    links = []
    links.append('<%s?action=restart>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#restart' % server_id)
    links.append('<%s?action=start>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#start' % server_id)
    links.append('<%s?action=stop>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#stop' % server_id)
    links.append('<%s?action=suspend>; rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#suspend' % server_id)

    result = []
    for c in cats:
        result.append(("Category", c))
    for l in links:
        result.append(("Link", l))
    for a in attrs:
        result.append(("X-OCCI-Attribute", a))
    return result


class TestComputeController(test_middleware.TestMiddleware):
    """Test OCCI compute controller."""

    def test_list_vms_empty(self):
        tenant = fakes.tenants["bar"]
        app = self.get_app()

        req = self._build_req("/compute", tenant["id"], method="GET")

        m = mock.MagicMock()
        m.user.project_id = tenant["id"]
        req.environ["keystone.token_auth"] = m

        resp = req.get_response(app)

        self.assertEqual("/%s/servers" % tenant["id"], req.path_info)

        expected_result = ""
        self.assertContentType(resp)
        self.assertExpectedResult(expected_result, resp)
        self.assertEqual(200, resp.status_code)

    def test_list_vms_one_vm(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        req = self._build_req("/compute", tenant["id"], method="GET")

        resp = req.get_response(app)

        self.assertEqual("/%s/servers" % tenant["id"], req.path_info)

        self.assertEqual(200, resp.status_code)
        expected = []
        for s in fakes.servers[tenant["id"]]:
            expected.append(("X-OCCI-Location", "/compute/%s" % s["id"]))
        self.assertExpectedResult(expected, resp)

    def test_show_vm(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for server in fakes.servers[tenant["id"]]:
            req = self._build_req("/compute/%s" % server["id"],
                                  tenant["id"], method="GET")

            resp = req.get_response(app)
            expected = build_occi_server(server)
            self.assertContentType(resp)
            self.assertExpectedResult(expected, resp)
            self.assertEqual(200, resp.status_code)

    def test_vm_not_found(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/compute/%s" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_create_vm(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        headers = {
            'Category': (
                'compute;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind",'
                'foo;'
                'scheme="http://schemas.openstack.org/template/resource#";'
                'class="mixin",'
                'bar;'
                'scheme="http://schemas.openstack.org/template/os#";'
                'class="mixin"')
        }
        req = self._build_req("/compute", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)

        expected = [("X-OCCI-Location", "/compute/%s" % "foo")]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertContentType(resp)


class ComputeControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                 TestComputeController):
    """Test OCCI compute controller with Accept: text/plain."""


class ComputeControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                TestComputeController):
    """Test OCCI compute controller with Accept: text/occi."""
