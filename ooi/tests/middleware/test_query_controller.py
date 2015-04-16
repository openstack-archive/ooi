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


from ooi.tests import fakes
from ooi.tests.middleware import test_middleware


class TestQueryController(test_middleware.TestMiddleware):
    """Test OCCI query controller."""

    def test_query(self):
        tenant_id = fakes.tenants["bar"]["id"]
        result = self._build_req("/-/", tenant_id).get_response(self.get_app())
        self.assertDefaults(result)
        self.assertExpectedResult(fakes.fake_query_results(), result)
        self.assertEqual(200, result.status_code)


class QueryControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                               TestQueryController):
    """Test OCCI query controller with Accept: text/plain."""


class QueryControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                              TestQueryController):
    """Test OCCI query controller with Accept: text/cci."""
