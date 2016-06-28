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

import webob
import webob.dec
import webob.exc

from ooi import exception
from ooi.tests import base
from ooi import wsgi


class TestResourceExceptionHandler(base.TestCase):
    def test_invalid(self):
        ret = self.return_fault_with_handler(exception.Invalid)
        self.assertIsInstance(ret, wsgi.Fault)
        self.assertIsInstance(ret.wrapped_exc, webob.exc.WSGIHTTPException)
        self.assertEqual(400, ret.wrapped_exc.code)

    def test_not_implemented(self):
        ret = self.return_fault_with_handler(exception.NotImplemented)
        self.assertIsInstance(ret, wsgi.Fault)
        self.assertEqual(webob.exc.HTTPNotImplemented.code,
                         ret.wrapped_exc.code)

    def test_bad_request(self):
        ret = self.return_fault_with_handler(TypeError)
        self.assertIsInstance(ret, wsgi.Fault)
        self.assertIsInstance(ret.wrapped_exc, webob.exc.HTTPBadRequest)

    def test_fault(self):
        fault = wsgi.Fault(webob.exc.HTTPInternalServerError())
        ret = self.return_fault_with_handler(fault)
        self.assertIs(ret, fault)

    def test_http_exception(self):
        ret = self.return_fault_with_handler(webob.exc.HTTPNotFound())
        self.assertIsInstance(ret, wsgi.Fault)
        self.assertIsInstance(ret.wrapped_exc, webob.exc.HTTPNotFound)

    def test_internal_server_error(self):
        ret = self.return_fault_with_handler(Exception)
        self.assertIsInstance(ret, wsgi.Fault)
        self.assertIsInstance(ret.wrapped_exc,
                              webob.exc.HTTPInternalServerError)

    @staticmethod
    def return_fault_with_handler(ex):
        try:
            with wsgi.ResourceExceptionHandler():
                raise ex
        except wsgi.Fault as e:
            return e
