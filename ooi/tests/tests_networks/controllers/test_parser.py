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

from ooi.tests import base
from ooi.wsgi.networks import parsers
from  ooi.wsgi.parsers import HeaderParser


class TestParser(base.TestCase):
    """Test OpenStack Driver against DevStack."""

    def setUp(self):
        super(TestParser, self).setUp()
       # self.driver = OpenStackNet

    def test_query_string(self): #TODO(jorgesece): the fake driver should be improved to make parametriced query tests
        query = parsers.get_query_string({"tenant_id" : "foo", "name" : "public"})

        self.assertEqual(25, query.__len__())

    def test_param_from_headers(self): #TODO(jorgesece): the fake driver should be improved to make parametriced query tests
        tenant_id="33"
        headers = {
            'Category': 'network; scheme="http://schema#";class="kind";',
            'X-OCCI-Attribute': 'tenant_id=%s, network_id=1' % tenant_id,
        }

        #TextParse from ooi.wsgi I can use well. I will come back to it
        parsed = HeaderParser(headers, None).parse()
        parameters = parsed["attributes"]
        self.assertEqual(2,parameters.__len__())
        self.assertEqual(tenant_id, parameters['tenant_id'])

    def test_param_from_headers_mixin(self):
        tenant_id = "33"
        mixin_id = "mixinID"
        mixin_scheme = "http://subnet#"
        network_term = "network"
        network_scheme = "http://schema#"
        headers = {
            'Category': '%s; scheme="%s";class="kind",' % (network_term, network_scheme) +
            '%s; scheme="%s"; class=mixin' % (mixin_id, mixin_scheme),
            'X-OCCI-Attribute': 'tenant_id=%s, network_id=1' % tenant_id,
        }
        parameters = HeaderParser(headers, None).parse()
        attributes = parameters["attributes"]
        self.assertEqual(2, attributes.__len__())
        self.assertEqual(tenant_id, attributes['tenant_id'])
        self.assertIn(mixin_scheme, parameters["schemes"])
        self.assertEquals( '%s%s' % (network_scheme, network_term), parameters["category"])

    def test_make_body(self):
        parameters = {"tenant_id" : "foo", "name" : "public"}
        body = parsers.make_body("network", parameters)

        self.assertIsNotNone(body["network"])
        self.assertEqual(2, body["network"].__len__())


