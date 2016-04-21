# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
# Copyright 2016 LIP - Lisbon
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

from ooi.api import network_link
from ooi import exception
from ooi.occi.core import collection
from ooi.tests import fakes_neutron as fakes
from ooi.tests.middleware import test_middleware
from ooi import utils
from ooi import wsgi


class TestNetInterfaceController(test_middleware.TestMiddleware):
    """Test OCCI network interface controller."""
    def setUp(self):
        super(TestNetInterfaceController, self).setUp()
        self.accept = self.content_type = None
        self.application_url = fakes.application_url
        self.app = wsgi.OCCIMiddleware(None)

    @mock.patch.object(network_link.Controller, "index")
    def test_list_ifaces_empty(self, mock_index):
        tenant = fakes.tenants["bar"]
        mock_index.return_value = fakes.fake_network_link_occi(
            fakes.network_links[tenant['id']]
        )
        for url in ("/networklink/", "/networklink"):
            req = self._build_req(url, tenant["id"], method="GET")

            req.environ["HTTP_X_PROJECT_ID"] = tenant["id"]

            resp = req.get_response(self.app)

            expected_result = ""
            self.assertContentType(resp)
            self.assertExpectedResult(expected_result, resp)
            self.assertEqual(204, resp.status_code)

    @mock.patch.object(network_link.Controller, "index")
    def test_list_ifaces(self, mock_index):
        tenant = fakes.tenants["foo"]
        mock_index.return_value = collection.Collection(
            fakes.fake_network_link_occi(
                fakes.network_links[tenant['id']]
            )
        )

        for url in ("/networklink/", "/networklink"):
            req = self._build_req(url, tenant["id"], method="GET")

            resp = req.get_response(self.app)

            self.assertEqual(200, resp.status_code)
            expected = []
            for ip in fakes.network_links[tenant["id"]]:
                if ip["instance_id"]:
                    # fixme(jorgesece): test in case of instance None
                    link_id = '_'.join([ip["instance_id"],
                                        ip["network_id"],
                                        ip["ip"]])
                    expected.append(
                        ("X-OCCI-Location",
                         utils.join_url(self.application_url + "/",
                                        "networklink/%s" % link_id))
                    )
            self.assertExpectedResult(expected, resp)

    @mock.patch.object(network_link.Controller, "show")
    def test_show_iface(self, m_show):
        tenant = fakes.tenants["foo"]
        m_show.return_value = fakes.fake_network_link_occi(
            fakes.network_links[tenant['id']]
        )

        for ip in fakes.network_links[tenant["id"]]:
            if ip["instance_id"] is not None:
                link_id = '_'.join([ip["instance_id"],
                                    ip["network_id"],
                                    ip["ip"]]
                                   )
                req = self._build_req("/networklink/%s" % link_id,
                                      tenant["id"], method="GET")

                resp = req.get_response(self.app)
                self.assertContentType(resp)
    #     net_id = uuid.uuid4().hex

                source = utils.join_url(self.application_url + "/",
                                        "compute/%s" % ip["instance_id"])
                target = utils.join_url(self.application_url + "/",
                                        "network/%s" % ip['network_id'])
                self.assertResultIncludesLinkAttr(link_id, source, target,
                                                  resp)
                self.assertEqual(200, resp.status_code)

    @mock.patch.object(network_link.Controller, "show")
    def test_show_invalid_id(self, m_show):
        tenant = fakes.tenants["foo"]
        link_id = uuid.uuid4().hex
        m_show.side_effect = exception.LinkNotFound(link_id=link_id)
        req = self._build_req("/networklink/%s" % link_id,
                              tenant["id"], method="GET")
        resp = req.get_response(self.app)
        self.assertEqual(404, resp.status_code)

    @mock.patch.object(network_link.Controller, "create")
    def test_create_link_invalid(self, m_create):
        tenant = fakes.tenants["foo"]
        m_create.side_effect = exception.Invalid
        net_id = fakes.network_links[tenant['id']][0]['network_id']
        occi_net_id = utils.join_url(self.application_url + "/",
                                     "network/%s" % net_id)
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.core.source="foo", '
                'occi.core.target="%s"'
            ) % occi_net_id
        }
        req = self._build_req("/networklink", None, method="POST",
                              headers=headers)
        resp = req.get_response(self.app)
        self.assertEqual(400, resp.status_code)

    @mock.patch.object(network_link.Controller, "create")
    def test_create_link_no_pool(self, m_create):
        tenant = fakes.tenants["foo"]
        m_create.return_value = fakes.fake_network_link_occi(
            fakes.network_links[tenant['id']]
        )[0]
        net_id = fakes.network_links[tenant['id']][0]['network_id']
        occi_net_id = utils.join_url(self.application_url + "/",
                                     "network/%s" % net_id)
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind"'),
            'X-OCCI-Attribute': (
                'occi.core.source="foo", '
                'occi.core.target="%s"'
            ) % occi_net_id
        }
        req = self._build_req("/networklink", None, method="POST",
                              headers=headers)
        resp = req.get_response(self.app)
        self.assertEqual(200, resp.status_code)

    @mock.patch.object(network_link.Controller, "create")
    def test_create_link_with_pool(self, m_create):
        tenant = fakes.tenants["foo"]
        m_create.return_value = collection.Collection(
            [fakes.fake_network_link_occi(
                fakes.network_links[tenant['id']]
            )[0]])
        link_info = fakes.network_links[tenant['id']][0]

        server_url = utils.join_url(self.application_url + "/",
                                    "compute/%s" % link_info['instance_id'])
        net_url = utils.join_url(self.application_url + "/",
                                 "network/%s" % link_info['network_id'])
        pool_name = 'pool'
        headers = {
            'Category': (
                'networkinterface;'
                'scheme="http://schemas.ogf.org/occi/infrastructure#";'
                'class="kind",'
                '%s;'
                'scheme="http://schemas.openstack.org/network/'
                'floatingippool#"; class="mixin"') % pool_name,
            'X-OCCI-Attribute': (
                'occi.core.source="%s", '
                'occi.core.target="%s"'
            ) % (server_url, net_url)
        }
        req = self._build_req("/networklink", tenant["id"], method="POST",
                              headers=headers)
        resp = req.get_response(self.app)

        link_id = '_'.join([link_info['instance_id'],
                            link_info['network_id'],
                            link_info['ip']])
        expected = [("X-OCCI-Location",
                     utils.join_url(self.application_url + "/",
                                    "networklink/%s" % link_id))]
        self.assertEqual(200, resp.status_code)
        self.assertExpectedResult(expected, resp)
        self.assertDefaults(resp)

    @mock.patch.object(network_link.Controller, "delete")
    def test_delete_fixed(self, m_delete):
        tenant = fakes.tenants["foo"]
        m_delete.return_value = []

        for n in fakes.network_links[tenant["id"]]:
            if n["network_id"] != "PUBLIC":
                if n["instance_id"]:
                    link_id = '_'.join([n["instance_id"],
                                        n["network_id"],
                                        n["ip"]])
                    req = self._build_req("/networklink/%s" % link_id,
                                          tenant["id"], method="DELETE")
                    resp = req.get_response(self.app)
                    self.assertContentType(resp)
                    self.assertEqual(204, resp.status_code)

    @mock.patch.object(network_link.Controller, "delete")
    def test_delete_public(self, m_delete):
        tenant = fakes.tenants["public"]
        m_delete.return_value = []

        for n in fakes.network_links[tenant["id"]]:
            if n["network_id"] != "PUBLIC":
                if n["instance_id"]:
                    link_id = '_'.join([n["instance_id"],
                                        n["network_id"],
                                        n["ip"]])
                    req = self._build_req("/networklink/%s" % link_id,
                                          tenant["id"], method="DELETE")
                    resp = req.get_response(self.app)
                    self.assertContentType(resp)
                    self.assertEqual(204, resp.status_code)


class NetInterfaceControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                                      TestNetInterfaceController):
    """Test OCCI network link controller with Accept: text/plain."""


class NetInterfaceControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                                     TestNetInterfaceController):
    """Test OCCI network link controller with Accept: text/occi."""
