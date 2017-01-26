# -*- coding: utf-8 -*-

# Copyright 2015 LIP - INDIGO-DataCloud
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

from ooi.tests import fakes
from ooi.tests.functional.middleware import test_middleware
from ooi import utils


def build_occi_ip_reservation(ip, application_url):
    name = ip["pool"]
    network_id = ip["id"]
    address = ip["ip"]
    if ip["instance_id"]:
        used = str(True).lower()
    else:
        used = str(False).lower()
    cats = []
    cats.append('ipreservation; '
                'scheme='
                '"http://schemas.ogf.org/occi/infrastructure#";'
                ' class="kind"; title="IPReservation"; rel='
                '"http://schemas.ogf.org/occi/infrastructure#network";'
                ' location="%s/ipreservation/"' % application_url)
    links = []
    links.append('<%s/ipreservation/%s?action=up>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#up"' %
                 (application_url, network_id))
    links.append('<%s/ipreservation/%s?action=down>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#down"' %
                 (application_url, network_id))

    attrs = [
        'occi.core.title="%s"' % name,
        'occi.core.id="%s"' % network_id,
        'occi.ipreservation.address="%s"' % address,
        'occi.ipreservation.used="%s"' % used,
        ]
    result = []
    for c in cats:
        result.append(("Category", c))
    for a in attrs:
        result.append(("X-OCCI-Attribute", a))
    for l in links:
        result.append(("Link", l))
    return result


class TestNetIPReservationController(test_middleware.TestMiddleware):
    """Test OCCI IP Reservation controller."""
    def setUp(self):
        super(TestNetIPReservationController, self).setUp()
        self.application_url = fakes.application_url
        self.app = self.get_app()

    def test_list_empty(self):
        tenant = fakes.tenants["bar"]

        for url in ("/ipreservation/", "/ipreservation"):
            req = self._build_req(url, tenant["id"], method="GET")

            req.environ["HTTP_X_PROJECT_ID"] = tenant["id"]

            resp = req.get_response(self.app)

            expected_result = ""
            self.assertContentType(resp)
            self.assertExpectedResult(expected_result, resp)
            self.assertEqual(204, resp.status_code)

    def test_list(self):
        tenant = fakes.tenants["baz"]

        for url in ("/ipreservation/", "/ipreservation"):
            req = self._build_req(url, tenant["id"], method="GET")
            resp = req.get_response(self.app)

            self.assertEqual(200, resp.status_code)
            expected = []
            for ip in fakes.floating_ips[tenant["id"]]:
                expected.append(
                    ("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "ipreservation/%s" % ip["id"]))
                )

            self.assertExpectedResult(expected, resp)

    def test_show(self):
        tenant = fakes.tenants["baz"]
        for ip in fakes.floating_ips[tenant["id"]]:
            ip_id = ip["id"]
            req = self._build_req("/ipreservation/%s" % ip_id,
                                  tenant["id"], method="GET")

            resp = req.get_response(self.app)
            self.assertContentType(resp)
            self.assertEqual(200, resp.status_code)
            expected = build_occi_ip_reservation(
                ip,
                self.application_url)
            self.assertExpectedResult(expected, resp)

    def test_show_invalid_id(self):
        tenant = fakes.tenants["foo"]
        link_id = uuid.uuid4().hex
        req = self._build_req("/ipreservation/%s" % link_id,
                              tenant["id"], method="GET")
        resp = req.get_response(self.app)
        self.assertEqual(404, resp.status_code)

    def test_delete(self):
        tenant = fakes.tenants["foo"]
        link_id = uuid.uuid4().hex
        req = self._build_req("/ipreservation/%s" % link_id,
                              tenant["id"], method="DELETE")
        resp = req.get_response(self.app)
        self.assertEqual(204, resp.status_code)

    def test_create(self):
        tenant = fakes.tenants["baz"]
        ip_id = fakes.allocated_ip["id"]
        headers = {
            'Category': 'ipreservation;'
                        ' scheme='
                        '"http://schemas.ogf.org/occi/infrastructure#";'
                        'class="kind",'
        }
        req = self._build_req("/ipreservation/",
                              tenant["id"],
                              method="POST",
                              headers=headers)
        resp = req.get_response(self.app)
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "ipreservation/%s" % ip_id))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)

    def test_create_with_pool(self):
        tenant = fakes.tenants["baz"]
        ip_id = fakes.allocated_ip["id"]
        pool_name = "public"
        headers = {
            'Category': ('ipreservation;'
                         ' scheme='
                         '"http://schemas.ogf.org/occi/infrastructure#";'
                         'class="kind",'
                         '%s;'
                         'scheme="http://schemas.openstack.org/network/'
                         'floatingippool#"; class="mixin"') % pool_name,
        }
        req = self._build_req("/ipreservation/",
                              tenant["id"],
                              method="POST",
                              headers=headers)
        resp = req.get_response(self.app)
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "ipreservation/%s" % ip_id))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)