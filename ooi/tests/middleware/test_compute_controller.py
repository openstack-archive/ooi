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
from ooi import utils


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
                'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
                'class="kind"'),
    cats.append('%s; '
                'scheme="http://schemas.openstack.org/template/os#"; '
                'class="mixin"' % image_id),
    cats.append('%s; '
                'scheme="http://schemas.openstack.org/template/resource#"; '
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
    links.append('<%s/compute/%s?action=restart>; '
                 'rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#restart' %
                 (fakes.application_url, server_id))
    links.append('<%s/compute/%s?action=start>; '
                 'rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#start' %
                 (fakes.application_url, server_id))
    links.append('<%s/compute/%s?action=stop>; '
                 'rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#stop' %
                 (fakes.application_url, server_id))
    links.append('<%s/compute/%s?action=suspend>; '
                 'rel=http://schemas.ogf.org/occi/'
                 'infrastructure/compute/action#suspend' %
                 (fakes.application_url, server_id))

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

        for url in ("/compute/", "/compute"):
            req = self._build_req(url, tenant["id"], method="GET")

            m = mock.MagicMock()
            m.user.project_id = tenant["id"]
            req.environ["keystone.token_auth"] = m

            resp = req.get_response(app)

            expected_result = ""
            self.assertDefaults(resp)
            self.assertExpectedResult(expected_result, resp)
            self.assertEqual(204, resp.status_code)

    def test_list_vms(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for url in ("/compute/", "/compute"):
            req = self._build_req(url, tenant["id"], method="GET")

            resp = req.get_response(app)

            self.assertEqual(200, resp.status_code)
            expected = []
            for s in fakes.servers[tenant["id"]]:
                expected.append(
                    ("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "compute/%s" % s["id"]))
                )
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)

    def test_show_vm(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for server in fakes.servers[tenant["id"]]:
            req = self._build_req("/compute/%s" % server["id"],
                                  tenant["id"], method="GET")

            resp = req.get_response(app)
            expected = build_occi_server(server)
            self.assertDefaults(resp)
            self.assertExpectedResult(expected, resp)
            self.assertEqual(200, resp.status_code)

    def test_vm_not_found(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        req = self._build_req("/compute/%s" % uuid.uuid4().hex,
                              tenant["id"], method="GET")
        resp = req.get_response(app)
        self.assertEqual(404, resp.status_code)

    def test_action_vm(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        for action in ("stop", "start", "restart"):
            headers = {
                'Category': (
                    '%s;'
                    'scheme="http://schemas.ogf.org/occi/infrastructure/'
                    'compute/action#";'
                    'class="action"' % action)
            }
            for server in fakes.servers[tenant["id"]]:
                req = self._build_req("/compute/%s?action=%s" % (server["id"],
                                                                 action),
                                      tenant["id"], method="POST",
                                      headers=headers)
                resp = req.get_response(app)
                self.assertDefaults(resp)
                self.assertEqual(204, resp.status_code)

    def test_invalid_action(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        action = "foo"
        for server in fakes.servers[tenant["id"]]:
            req = self._build_req("/compute/%s?action=%s" % (server["id"],
                                                             action),
                                  tenant["id"], method="POST")
            resp = req.get_response(app)
            self.assertDefaults(resp)
            self.assertEqual(400, resp.status_code)

    def test_action_body_mismatch(self):
        tenant = fakes.tenants["foo"]
        app = self.get_app()

        action = "stop"
        headers = {
            'Category': (
                'start;'
                'scheme="http://schemas.ogf.org/occi/infrastructure/'
                'compute/action#";'
                'class="action"')
        }
        for server in fakes.servers[tenant["id"]]:
            req = self._build_req("/compute/%s?action=%s" % (server["id"],
                                                             action),
                                  tenant["id"], method="POST",
                                  headers=headers)
            resp = req.get_response(app)
            self.assertDefaults(resp)
            self.assertEqual(400, resp.status_code)

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

        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "compute/%s" % "foo"))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertDefaults(resp)

    def test_create_vm_incomplete(self):
        tenant = fakes.tenants["foo"]

        app = self.get_app()
        headers = {
            'Category': (
                'compute;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind",'
                'bar;'
                'scheme="http://schemas.openstack.org/template/os#";'
                'class="mixin"')
        }

        req = self._build_req("/compute", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)

        self.assertEqual(400, resp.status_code)
        self.assertDefaults(resp)

    def test_create_with_context(self):
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
                'class="mixin",'
                'user_data;'
                'scheme="http://schemas.openstack.org/compute/instance#";'
                'class="mixin"'
            ),
            'X-OCCI-Attribute': (
                'org.openstack.compute.user_data="foo"'
            )
        }

        req = self._build_req("/compute", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(app)

        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "compute/%s" % "foo"))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertDefaults(resp)

    def test_vm_links(self):
        tenant = fakes.tenants["baz"]

        app = self.get_app()

        for server in fakes.servers[tenant["id"]]:
            req = self._build_req("/compute/%s" % server["id"],
                                  tenant["id"], method="GET")

            resp = req.get_response(app)

            vol_id = server["os-extended-volumes:volumes_attached"][0]["id"]
            link_id = '_'.join([server["id"], vol_id])

            self.assertDefaults(resp)
            self.assertResultIncludesLink(link_id, server["id"], vol_id, resp)
            self.assertEqual(200, resp.status_code)


class ComputeControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                 TestComputeController):
    """Test OCCI compute controller with Accept: text/plain."""


class ComputeControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                TestComputeController):
    """Test OCCI compute controller with Accept: text/occi."""
