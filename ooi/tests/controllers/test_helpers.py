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

from ooi.api import helpers
from ooi.tests import base
from ooi.tests import fakes

import six
import webob.exc


class TestExceptionHelper(base.TestCase):
    @staticmethod
    def get_fault(code):
        return {
            "computeFault": {
                "code": code,
                "message": "Fault!",
                "details": "Error Details..."
            }
        }

    def test_exception(self):
        code_and_exception = {
            400: webob.exc.HTTPBadRequest,
            401: webob.exc.HTTPUnauthorized,
            403: webob.exc.HTTPForbidden,
            404: webob.exc.HTTPNotFound,
            405: webob.exc.HTTPMethodNotAllowed,
            406: webob.exc.HTTPNotAcceptable,
            409: webob.exc.HTTPConflict,
            413: webob.exc.HTTPRequestEntityTooLarge,
            415: webob.exc.HTTPUnsupportedMediaType,
            429: webob.exc.HTTPTooManyRequests,
            501: webob.exc.HTTPNotImplemented,
            503: webob.exc.HTTPServiceUnavailable,
            # Any other thing should be a 500
            500: webob.exc.HTTPInternalServerError,
            507: webob.exc.HTTPInternalServerError,
        }

        for code, exception in six.iteritems(code_and_exception):
            fault =  self.get_fault(code)
            resp = fakes.create_fake_json_resp(fault, code)
            ret = helpers.exception_from_response(resp)
            self.assertIsInstance(ret, exception)
            self.assertEqual(fault["computeFault"]["message"], ret.explanation)

    def test_error_handling_exception(self):
        fault = {}
        resp = fakes.create_fake_json_resp(fault, 404)
        ret = helpers.exception_from_response(resp)
        self.assertIsInstance(ret, webob.exc.HTTPInternalServerError)
