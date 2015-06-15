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

from ooi.tests import base
from ooi.tests import fakes


class TestController(base.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestController, self).__init__(*args, **kwargs)

    def setUp(self):
        super(TestController, self).setUp()
        self.application_url = fakes.application_url

    def assertExpectedReq(self, method, path, body, request):
        self.assertEqual(method, request.method)
        self.assertEqual(path, request.path_info)
        self.assertEqual(body, request.text)
