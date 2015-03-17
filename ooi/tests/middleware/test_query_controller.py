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


from ooi.tests.middleware import test_middleware


class TestQueryController(test_middleware.TestMiddleware):
    """Test OCCI query controller."""

    def test_query(self):
        result = self._build_req("/-/").get_response(self.app)

        expected_result = [
            ('Category', 'start; scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; class="action"'),  # noqa
            ('Category', 'stop; scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; class="action"'),  # noqa
            ('Category', 'restart; scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; class="action"'),  # noqa
            ('Category', 'suspend; scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; class="action"'),  # noqa
        ]

        self.assertContentType(result)
        self.assertExpectedResult(expected_result, result)
        self.assertEqual(200, result.status_code)


class QueryControllerTextPlain(test_middleware.TestMiddlewareTextPlain,
                               TestQueryController):
    """Test OCCI query controller with Accept: text/plain."""


class QueryControllerTextOcci(test_middleware.TestMiddlewareTextOcci,
                              TestQueryController):
    """Test OCCI query controller with Accept: text/cci."""
