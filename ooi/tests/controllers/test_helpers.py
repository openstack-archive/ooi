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

import json
import uuid

import mock
import six
import webob

from ooi.api import helpers
from ooi.tests import base
from ooi.tests import fakes

import webob.exc


class TestIDGetter(base.TestCase):
    def test_resolve_id_relative_url(self):
        res_url = uuid.uuid4().hex
        base_url = "http://foobar.com/foo"
        r = helpers._resolve_id(base_url, res_url)
        self.assertEqual(base_url, r[0])
        self.assertEqual(res_url, r[1])

    def test_resolve_id_absolute(self):
        res_id = uuid.uuid4().hex
        res_url = "/%s" % res_id
        base_url = "http://foobar.com/foo"
        r = helpers._resolve_id(base_url, res_url)
        self.assertEqual("http://foobar.com/", r[0])
        self.assertEqual(res_id, r[1])

    def test_resolve_id_no_resource_url(self):
        base_url = "http://foobar.com/foo"
        r = helpers._resolve_id(base_url, "")
        self.assertEqual(base_url, r[0])
        self.assertEqual("", r[1])

    def test_get_id_no_kind_relative(self):
        req_url = '/foo'
        req = webob.Request.blank(req_url)
        res_url = "%s" % uuid.uuid4().hex
        r = helpers.get_id_with_kind(req, res_url)
        self.assertEqual('%s%s' % (req.application_url, req_url), r[0])
        self.assertEqual(res_url, r[1])

    def test_get_id_no_kind_absolute(self):
        req_url = '/foo'
        req = webob.Request.blank(req_url)
        res_id = uuid.uuid4().hex
        res_url = "/bar/%s" % res_id
        r = helpers.get_id_with_kind(req, res_url)
        self.assertEqual('%s/bar' % (req.application_url), r[0])
        self.assertEqual(res_id, r[1])

    def test_get_id_kind_matching(self):
        m = mock.MagicMock()
        m.location = "foo/"
        req_url = "/foo"
        req = webob.Request.blank(req_url)
        res_url = "%s" % uuid.uuid4().hex
        r = helpers.get_id_with_kind(req, res_url, m)
        self.assertEqual("%s%s" % (req.application_url, req_url), r[0])
        self.assertEqual(res_url, r[1])

    def test_get_id_kind_not_matching(self):
        m = mock.MagicMock()
        m.location = "foo/"
        req_url = "/foo"
        req = webob.Request.blank(req_url)
        from ooi import exception
        self.assertRaises(exception.Invalid,
                          helpers.get_id_with_kind,
                          req, "/bar/baz", m)


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
            fault = self.get_fault(code)
            resp = fakes.create_fake_json_resp(fault, code)
            ret = helpers.exception_from_response(resp)
            self.assertIsInstance(ret, exception)
            self.assertEqual(fault["computeFault"]["message"], ret.explanation)

    def test_error_handling_exception(self):
        fault = {}
        resp = fakes.create_fake_json_resp(fault, 404)
        ret = helpers.exception_from_response(resp)
        self.assertIsInstance(ret, webob.exc.HTTPInternalServerError)


class TestBaseHelper(base.TestController):
    def setUp(self):
        super(TestBaseHelper, self).setUp()
        self.version = "version foo bar baz"
        self.helper = helpers.OpenStackHelper(mock.MagicMock(), self.version)

    def assertExpectedReq(self, method, path, body, request):
        self.assertEqual(method, request.method)
        self.assertEqual(path, request.path_info)
        if body and request.content_type == "application/json":
            self.assertDictEqual(body, request.json_body)
        else:
            self.assertEqual(body, request.text)

    def test_new_request(self):
        req = webob.Request.blank("foo")
        new_req = self.helper._get_req(req, method="GET")
        self.assertEqual(self.version, new_req.script_name)
        self.assertEqual("foo", new_req.path_info)
        self.assertIsNot(req, new_req)

    def test_new_request_with_path(self):
        req = webob.Request.blank("foo")
        new_req = self.helper._get_req(req, path="bar", method="GET")
        self.assertEqual("bar", new_req.path_info)
        self.assertExpectedReq("GET", "bar", "", new_req)

    def test_new_request_with_body(self):
        req = webob.Request.blank("foo")
        body = {"bar": 1}
        new_req = self.helper._get_req(req, body=json.dumps(body),
                                       method="POST")
        self.assertExpectedReq("POST", "foo", body, new_req)

    def test_new_request_with_content_type(self):
        req = webob.Request.blank("foo")
        new_req = self.helper._get_req(req, content_type="foo/bar",
                                       method="GET")
        self.assertEqual("foo/bar", new_req.content_type)

    def test_get_from_response(self):
        d = {"element": {"foo": "bar"}}
        body = json.dumps(d)
        response = webob.Response(status=200, body=body)
        result = self.helper.get_from_response(response,
                                               "element",
                                               {})
        self.assertEqual(d["element"], result)

    def test_get_from_response_with_default(self):
        d = {"element": {"foo": "bar"}}
        body = json.dumps({})
        response = webob.Response(status=200, body=body)
        result = self.helper.get_from_response(response,
                                               "element",
                                               d["element"])
        self.assertEqual(d["element"], result)

    def test_get_from_response_with_exception(self):
        d = {"unauthorized": {"message": "unauthorized"}}
        body = json.dumps(d)
        response = webob.Response(status=403, body=body)
        self.assertRaises(webob.exc.HTTPForbidden,
                          self.helper.get_from_response,
                          response,
                          "foo",
                          {})


class TestOpenStackHelper(TestBaseHelper):
    @mock.patch.object(helpers.OpenStackHelper, "_get_index_req")
    def test_index(self, m):
        resp = fakes.create_fake_json_resp({"servers": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.index(None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_index_req")
    def test_index_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.index,
                          None)
        m.assert_called_with(None)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_flavors_req")
    def test_flavors(self, m):
        resp = fakes.create_fake_json_resp({"flavors": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_flavors(None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_flavors_req")
    def test_flavors_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_flavors,
                          None)
        m.assert_called_with(None)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_images_req")
    def test_images(self, m):
        resp = fakes.create_fake_json_resp({"images": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_images(None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_images_req")
    def test_images_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_images,
                          None)
        m.assert_called_with(None)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_volumes_req")
    def test_volumes(self, m):
        resp = fakes.create_fake_json_resp({"volumes": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_volumes(None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_volumes_req")
    def test_volumes_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_volumes,
                          None)
        m.assert_called_with(None)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_floating_ips_req")
    def test_floating_ips(self, m):
        resp = fakes.create_fake_json_resp({"floating_ips": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_floating_ips(None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_floating_ips_req")
    def test_floating_ips_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_floating_ips,
                          None)
        m.assert_called_with(None)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_floating_ip_pools_req")
    def test_floating_ip_pools(self, m):
        resp = fakes.create_fake_json_resp({"floating_ip_pools": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_floating_ip_pools(None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_floating_ip_pools_req")
    def test_floating_ip_pools_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_floating_ip_pools,
                          None)
        m.assert_called_with(None)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_flavors_req")
    def test_get_flavors(self, m):
        resp = fakes.create_fake_json_resp({"flavors": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.get_flavors(None)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_flavors_req")
    def test_get_flavors_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_flavors,
                          None)
        m.assert_called_with(None)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_delete_req")
    def test_delete(self, m):
        resp = fakes.create_fake_json_resp(None, 204)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        ret = self.helper.delete(None, server_uuid)
        self.assertIsNone(ret)
        m.assert_called_with(None, server_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_delete_req")
    def test_delete_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.delete,
                          None,
                          server_uuid)
        m.assert_called_with(None, server_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_volume_delete_req")
    def test_volume_delete(self, m):
        resp = fakes.create_fake_json_resp(None, 204)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        vol_uuid = uuid.uuid4().hex
        ret = self.helper.volume_delete(None, vol_uuid)
        self.assertIsNone(ret)
        m.assert_called_with(None, vol_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_volume_delete_req")
    def test_volume_delete_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        vol_uuid = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.volume_delete,
                          None,
                          vol_uuid)
        m.assert_called_with(None, vol_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_run_action_req")
    def test_run_action(self, m):
        resp = fakes.create_fake_json_resp(None, 202)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        action = "start"
        ret = self.helper.run_action(None, action, server_uuid)
        self.assertIsNone(ret)
        m.assert_called_with(None, action, server_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_run_action_req")
    def test_run_action_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        action = "bad action"
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.run_action,
                          None,
                          action,
                          server_uuid)
        m.assert_called_with(None, action, server_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_server_req")
    def test_get_server(self, m):
        resp = fakes.create_fake_json_resp({"server": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        ret = self.helper.get_server(None, server_uuid)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, server_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_server_req")
    def test_get_server_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_server,
                          None,
                          server_uuid)
        m.assert_called_with(None, server_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_image_req")
    def test_get_image(self, m):
        resp = fakes.create_fake_json_resp({"image": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        image_uuid = uuid.uuid4().hex
        ret = self.helper.get_image(None, image_uuid)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, image_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_image_req")
    def test_get_image_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        image_uuid = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_image,
                          None,
                          image_uuid)
        m.assert_called_with(None, image_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_flavor_req")
    def test_get_flavor(self, m):
        resp = fakes.create_fake_json_resp({"flavor": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        flavor_uuid = uuid.uuid4().hex
        ret = self.helper.get_flavor(None, flavor_uuid)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, flavor_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_flavor_req")
    def test_get_flavor_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        flavor_uuid = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_flavor,
                          None,
                          flavor_uuid)
        m.assert_called_with(None, flavor_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_volume_req")
    def test_get_volume(self, m):
        resp = fakes.create_fake_json_resp({"volume": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        volume_uuid = uuid.uuid4().hex
        ret = self.helper.get_volume(None, volume_uuid)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, volume_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_volume_req")
    def test_get_volume_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        volume_uuid = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_volume,
                          None,
                          volume_uuid)
        m.assert_called_with(None, volume_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_server_volumes_link_req")
    def test_get_server_volume_links(self, m):
        resp = fakes.create_fake_json_resp({"volumeAttachments": ["FOO"]}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        ret = self.helper.get_server_volumes_link(None, server_uuid)
        self.assertEqual(["FOO"], ret)
        m.assert_called_with(None, server_uuid)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_server_volumes_link_req")
    def test_get_server_volume_links_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.get_server_volumes_link,
                          None,
                          server_uuid)
        m.assert_called_with(None, server_uuid)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_create_server_req")
    def test_create_server(self, m):
        resp = fakes.create_fake_json_resp({"server": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        image = uuid.uuid4().hex
        flavor = uuid.uuid4().hex
        user_data = "foo"
        key_name = "wtfoo"
        bdm = []
        ret = self.helper.create_server(None, name, image, flavor,
                                        user_data=user_data,
                                        key_name=key_name,
                                        block_device_mapping_v2=bdm)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, name, image, flavor, user_data=user_data,
                             key_name=key_name, block_device_mapping_v2=bdm)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_create_server_req")
    def test_create_server_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        image = uuid.uuid4().hex
        flavor = uuid.uuid4().hex
        user_data = "foo"
        key_name = "wtfoo"
        bdm = []
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.create_server,
                          None,
                          name,
                          image,
                          flavor,
                          user_data=user_data,
                          key_name=key_name,
                          block_device_mapping_v2=bdm)
        m.assert_called_with(None, name, image, flavor, user_data=user_data,
                             key_name=key_name, block_device_mapping_v2=bdm)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_volume_create_req")
    def test_volume_create(self, m):
        resp = fakes.create_fake_json_resp({"volume": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        size = "10"
        ret = self.helper.volume_create(None, name, size)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, name, size)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_volume_create_req")
    def test_volume_create_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        size = "10"
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.volume_create,
                          None,
                          name,
                          size)
        m.assert_called_with(None, name, size)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_server_volumes_link_create_req")
    def test_create_servervolume_link(self, m):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_id = uuid.uuid4().hex
        vol_id = uuid.uuid4().hex
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.create_server_volumes_link,
                          None,
                          server_id,
                          vol_id)
        m.assert_called_with(None, server_id, vol_id, dev=None)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_server_volumes_link_create_req")
    def test_create_servervolume_with_exception(self, m):
        server_id = uuid.uuid4().hex
        vol_id = uuid.uuid4().hex

        raw_resp = {"volumeAttachment": {
            "device": "/dev/vdd",
            "id": "a26887c6-c47b-4654-abb5-dfadf7d3f803",
            "serverId": server_id,
            "volumeId": vol_id,
        }}
        resp = fakes.create_fake_json_resp(raw_resp, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ret = self.helper.create_server_volumes_link(None, server_id, vol_id)
        self.assertEqual(raw_resp["volumeAttachment"], ret)
        m.assert_called_with(None, server_id, vol_id, dev=None)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_server_volumes_link_delete_req")
    def test_delete_volume_link(self, m):
        resp = fakes.create_fake_json_resp(None, 202)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        vol_uuid = uuid.uuid4().hex
        ret = self.helper.delete_server_volumes_link(None,
                                                     server_uuid,
                                                     vol_uuid)
        self.assertIsNone(ret)
        m.assert_called_with(None, server_uuid, vol_uuid)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_server_volumes_link_delete_req")
    def test_delete_volume_link_w_exception(self, m):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        server_uuid = uuid.uuid4().hex
        vol_uuid = uuid.uuid4().hex
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.delete_server_volumes_link,
                          None,
                          server_uuid,
                          vol_uuid)
        m.assert_called_with(None, server_uuid, vol_uuid)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_floating_ip_allocate_req")
    def test_floating_ip_allocate(self, m_allocate):
        pool = "foo"
        resp = fakes.create_fake_json_resp({"floating_ip": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_allocate.return_value = req_mock
        ret = self.helper.allocate_floating_ip(None, pool)
        self.assertEqual("FOO", ret)
        m_allocate.assert_called_with(None, pool)

    @mock.patch.object(helpers.OpenStackHelper, "_get_floating_ip_release_req")
    def test_floating_ip_release(self, m):
        resp = fakes.create_fake_json_resp(None, 202)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ip_uuid = uuid.uuid4().hex
        ret = self.helper.release_floating_ip(None, ip_uuid)
        self.assertIsNone(ret)
        m.assert_called_with(None, ip_uuid)

    @mock.patch.object(helpers.OpenStackHelper, "_get_floating_ip_release_req")
    def test_floating_ip_release_w_exception(self, m):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ip_uuid = uuid.uuid4().hex
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.release_floating_ip,
                          None,
                          ip_uuid)
        m.assert_called_with(None, ip_uuid)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_associate_floating_ip_req")
    def test_associate_floating_ip(self, m):
        resp = fakes.create_fake_json_resp({"floating_ip": "FOO"}, 202)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ip = "192.168.0.20"
        server = uuid.uuid4().hex
        ret = self.helper.associate_floating_ip(None, server, ip)
        self.assertIsNone(ret)
        m.assert_called_with(None, server, ip)

    @mock.patch.object(helpers.OpenStackHelper, "_get_remove_floating_ip_req")
    def test_remove_floating_ip(self, m):
        resp = fakes.create_fake_json_resp(None, 202)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ip = "192.168.0.20"
        server = uuid.uuid4().hex
        ret = self.helper.remove_floating_ip(None, server, ip)
        self.assertIsNone(ret)
        m.assert_called_with(None, server, ip)

    @mock.patch.object(helpers.OpenStackHelper, "_get_remove_floating_ip_req")
    def test_remove_floating_ip_w_exception(self, m):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        ip = "192.168.0.20"
        server = uuid.uuid4().hex
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.remove_floating_ip,
                          None,
                          server,
                          ip)
        m.assert_called_with(None, server, ip)


class TestOpenStackHelperReqs(TestBaseHelper):
    def _build_req(self, tenant_id, **kwargs):
        environ = {"HTTP_X_PROJECT_ID": tenant_id}
        return webob.Request.blank("/whatever", environ=environ, **kwargs)

    def test_os_index_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_index_req(req)
        path = "/%s/servers" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_os_delete_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_delete_req(req, server_uuid)
        path = "/%s/servers/%s" % (tenant["id"], server_uuid)

        self.assertExpectedReq("DELETE", path, "", os_req)

    def test_os_volume_delete_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_volume_delete_req(req, server_uuid)
        path = "/%s/os-volumes/%s" % (tenant["id"], server_uuid)

        self.assertExpectedReq("DELETE", path, "", os_req)

    def test_os_action_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        server_uuid = uuid.uuid4().hex

        actions_map = {
            "stop": {"os-stop": None},
            "start": {"os-start": None},
            "suspend": {"suspend": None},
            "resume": {"resume": None},
            "unpause": {"unpause": None},
            "restart": {"reboot": {"type": "SOFT"}},
        }

        path = "/%s/servers/%s/action" % (tenant["id"], server_uuid)

        for act, body in six.iteritems(actions_map):
            os_req = self.helper._get_run_action_req(req, act, server_uuid)
            self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_server_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_server_req(req, server_uuid)
        path = "/%s/servers/%s" % (tenant["id"], server_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_flavors_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_flavors_req(req)
        path = "/%s/flavors/detail" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_flavor_req(self):
        tenant = fakes.tenants["foo"]
        flavor_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_flavor_req(req, flavor_uuid)
        path = "/%s/flavors/%s" % (tenant["id"], flavor_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_images_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_images_req(req)
        path = "/%s/images/detail" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_image_req(self):
        tenant = fakes.tenants["foo"]
        image_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_image_req(req, image_uuid)
        path = "/%s/images/%s" % (tenant["id"], image_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_volume_links_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_server_volumes_link_req(req, server_uuid)
        path = "/%s/servers/%s/os-volume_attachments" % (tenant["id"],
                                                         server_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_create_volume_links_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        vol_uuid = uuid.uuid4().hex
        dev = "foo"
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_server_volumes_link_create_req(req,
                                                                 server_uuid,
                                                                 vol_uuid,
                                                                 dev=dev)
        path = "/%s/servers/%s/os-volume_attachments" % (tenant["id"],
                                                         server_uuid)

        body = {"volumeAttachment": {"volumeId": vol_uuid, "device": dev}}
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_delete_volume_links_req(self):
        tenant = fakes.tenants["foo"]
        server_uuid = uuid.uuid4().hex
        vol_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_server_volumes_link_delete_req(req,
                                                                 server_uuid,
                                                                 vol_uuid)
        path = "/%s/servers/%s/os-volume_attachments/%s" % (tenant["id"],
                                                            server_uuid,
                                                            vol_uuid)

        self.assertExpectedReq("DELETE", path, "", os_req)

    def test_get_os_volumes_req(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_volumes_req(req)
        path = "/%s/os-volumes" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_volume_req(self):
        tenant = fakes.tenants["foo"]
        vol_uuid = uuid.uuid4().hex
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_volume_req(req, vol_uuid)
        path = "/%s/os-volumes/%s" % (tenant["id"], vol_uuid)

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_floating_ips(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_floating_ips_req(req)
        path = "/%s/os-floating-ips" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_floating_ip_pools(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        os_req = self.helper._get_floating_ip_pools_req(req)
        path = "/%s/os-floating-ip-pools" % tenant["id"]

        self.assertExpectedReq("GET", path, "", os_req)

    def test_get_os_get_server_create(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo server"
        image = "bar image"
        flavor = "baz flavor"

        body = {
            "server": {
                "name": name,
                "imageRef": image,
                "flavorRef": flavor,
            }
        }

        path = "/%s/servers" % tenant["id"]
        os_req = self.helper._get_create_server_req(req, name, image, flavor)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_get_server_create_with_user_data(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo server"
        image = "bar image"
        flavor = "baz flavor"
        user_data = "bazonk"

        body = {
            "server": {
                "name": name,
                "imageRef": image,
                "flavorRef": flavor,
                "user_data": user_data,
            },
        }

        path = "/%s/servers" % tenant["id"]
        os_req = self.helper._get_create_server_req(req, name, image, flavor,
                                                    user_data=user_data)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_get_server_create_with_key_name(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo server"
        image = "bar image"
        flavor = "baz flavor"
        key_name = "wtfoo"

        body = {
            "server": {
                "name": name,
                "imageRef": image,
                "flavorRef": flavor,
                "key_name": key_name,
            },
        }

        path = "/%s/servers" % tenant["id"]
        os_req = self.helper._get_create_server_req(req, name, image, flavor,
                                                    key_name=key_name)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_get_volume_create(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "foo server"
        size = "10"

        body = {
            "volume": {
                "display_name": name,
                "size": size
            }
        }

        path = "/%s/os-volumes" % tenant["id"]
        os_req = self.helper._get_volume_create_req(req, name, size)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_floating_ip_allocate(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        pool = "foo"
        body = {"pool": pool}
        path = "/%s/os-floating-ips" % tenant["id"]
        os_req = self.helper._get_floating_ip_allocate_req(req, pool)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_floating_ip_allocate_no_pool(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        pool = None
        body = {"pool": pool}
        path = "/%s/os-floating-ips" % tenant["id"]
        os_req = self.helper._get_floating_ip_allocate_req(req, pool)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_floating_ip_release(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        ip = uuid.uuid4().hex
        path = "/%s/os-floating-ips/%s" % (tenant["id"], ip)
        os_req = self.helper._get_floating_ip_release_req(req, ip)
        self.assertExpectedReq("DELETE", path, "", os_req)

    def test_get_os_associate_floating_ip(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        server = uuid.uuid4().hex
        ip = "192.168.0.20"
        body = {"addFloatingIp": {"address": ip}}
        path = "/%s/servers/%s/action" % (tenant["id"], server)
        os_req = self.helper._get_associate_floating_ip_req(req, server, ip)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_remove_floating_ip(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        server = uuid.uuid4().hex
        ip = "192.168.0.20"
        body = {"removeFloatingIp": {"address": ip}}
        path = "/%s/servers/%s/action" % (tenant["id"], server)
        os_req = self.helper._get_remove_floating_ip_req(req, server, ip)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_get_keypair_create(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "fookey"

        body = {
            "keypair": {
                "name": name,
            }
        }

        path = "/%s/os-keypairs" % tenant["id"]
        os_req = self.helper._get_keypair_create_req(req, name)
        self.assertExpectedReq("POST", path, body, os_req)

    def test_get_os_get_keypair_create_import(self):
        tenant = fakes.tenants["foo"]
        req = self._build_req(tenant["id"])
        name = "fookey"
        public_key = "fookeydata"

        body = {
            "keypair": {
                "name": name,
                "public_key": public_key
            }
        }

        path = "/%s/os-keypairs" % tenant["id"]
        os_req = self.helper._get_keypair_create_req(req, name,
                                                     public_key=public_key)
        self.assertExpectedReq("POST", path, body, os_req)

    @mock.patch.object(helpers.OpenStackHelper, "_get_keypair_create_req")
    def test_keypair_create(self, m):
        resp = fakes.create_fake_json_resp({"keypair": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        public_key = None
        ret = self.helper.keypair_create(None, name)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, name, public_key=public_key)

    @mock.patch.object(helpers.OpenStackHelper, "_get_keypair_create_req")
    def test_keypair_create_key_import(self, m):
        resp = fakes.create_fake_json_resp({"keypair": "FOO"}, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        public_key = "fookeydata"
        ret = self.helper.keypair_create(None, name, public_key=public_key)
        self.assertEqual("FOO", ret)
        m.assert_called_with(None, name, public_key=public_key)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_keypair_create_req")
    def test_keypair_create_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.keypair_create,
                          None,
                          name,
                          None)
        m.assert_called_with(None, name, public_key=None)
        m_exc.assert_called_with(resp)

    @mock.patch("ooi.api.helpers.exception_from_response")
    @mock.patch.object(helpers.OpenStackHelper, "_get_keypair_create_req")
    def test_keypair_create_key_import_with_exception(self, m, m_exc):
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(fault, 500)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m.return_value = req_mock
        name = uuid.uuid4().hex
        public_key = "fookeydata"
        m_exc.return_value = webob.exc.HTTPInternalServerError()
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.keypair_create,
                          None,
                          name,
                          public_key)
        m.assert_called_with(None, name, public_key=public_key)
        m_exc.assert_called_with(resp)

    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_create_port(self, m_tenant, m_create):
        ip = '22.0.0.1'
        net_id = uuid.uuid4().hex
        port_id = uuid.uuid4().hex
        mac = '890234'
        device_id = uuid.uuid4().hex
        p = {"interfaceAttachment": {
            "net_id": net_id,
            "port_id": port_id,
            "fixed_ips": [{"ip_address": ip}],
            "mac_addr": mac, "port_state": "ACTIVE"
        }}
        response = fakes.create_fake_json_resp(p, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = response
        m_create.return_value = req_mock
        ret = self.helper.create_port(None, net_id, device_id)
        self.assertEqual(device_id, ret['compute_id'])
        self.assertEqual(ip, ret['ip'])
        self.assertEqual(net_id, ret['network_id'])
        self.assertEqual(mac, ret['mac'])
        self.assertEqual(port_id, ret['ip_id'])

    @mock.patch.object(helpers.OpenStackHelper, "_get_ports")
    @mock.patch.object(helpers.OpenStackHelper, "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_delete_port(self, m_tenant, m_delete, m_ports):
        ip = '22.0.0.1'
        net_id = uuid.uuid4().hex
        mac = '890234'
        device_id = uuid.uuid4().hex
        port_id = uuid.uuid4().hex
        p = [{"net_id": net_id,
              "fixed_ips": [{"ip_address": ip}],
              "mac_addr": mac, "port_id": port_id
              }]
        m_ports.return_value = p
        response = fakes.create_fake_json_resp({}, 202)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = response
        m_delete.return_value = req_mock
        ret = self.helper.delete_port(None, device_id, mac)
        self.assertEqual([], ret)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_get_network_id(self, m_ten, m_req):
        m_ten.return_value = uuid.uuid4().hex
        mac = uuid.uuid4().hex
        device_id = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        ip = uuid.uuid4().hex
        p = {"interfaceAttachments": [
            {"net_id": net_id,
             "fixed_ips": [{"ip_address": ip}],
             "mac_addr": mac, "port_state": "ACTIVE"
             }]}
        resp = fakes.create_fake_json_resp(p, 200)
        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_req.return_value = req_mock
        ret = self.helper.get_network_id(None, mac, device_id)
        self.assertEqual(net_id, ret)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_get_network_id_empty(self, m_ten, m_req):
        m_ten.return_value = uuid.uuid4().hex
        mac = uuid.uuid4().hex
        device_id = uuid.uuid4().hex
        p = {"interfaceAttachments": []}
        resp = fakes.create_fake_json_resp(p, 200)

        req_mock = mock.MagicMock()
        req_mock.get_response.return_value = resp
        m_req.return_value = req_mock
        self.assertRaises(webob.exc.HTTPNotFound,
                          self.helper.get_network_id,
                          None,
                          mac,
                          device_id)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_associate_associate_err(self, m_ten, m_req):
        m_ten.return_value = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        device_id = uuid.uuid4().hex
        ip = uuid.uuid4().hex
        pool = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"floating_ip": {"ip": ip, "pool": pool}},
            202
        )
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp_ass = fakes.create_fake_json_resp(
            fault,
            500
        )
        req_all = mock.MagicMock()
        req_all.get_response.return_value = resp
        req_ass = mock.MagicMock()
        req_ass.get_response.return_value = resp_ass
        m_req.side_effect = [req_all,
                             req_ass]
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.assign_floating_ip,
                          None,
                          net_id, device_id)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_allocation_err(self, m_ten, m_req):
        m_ten.return_value = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        device_id = uuid.uuid4().hex
        fault = {"computeFault": {"message": "bad", "code": 500}}
        resp = fakes.create_fake_json_resp(
            fault,
            500
        )
        req_all = mock.MagicMock()
        req_all.get_response.return_value = resp
        m_req.side_effect = [req_all]
        self.assertRaises(webob.exc.HTTPInternalServerError,
                          self.helper.assign_floating_ip,
                          None,
                          net_id, device_id)

    @mock.patch.object(helpers.OpenStackHelper,
                       "_get_req")
    @mock.patch.object(helpers.OpenStackHelper, "tenant_from_req")
    def test_associate_floating_ip(self, m_ten, m_req):
        m_ten.return_value = uuid.uuid4().hex
        net_id = uuid.uuid4().hex
        device_id = uuid.uuid4().hex
        ip = uuid.uuid4().hex
        ip_id = uuid.uuid4().hex
        pool = uuid.uuid4().hex
        resp = fakes.create_fake_json_resp(
            {"floating_ip": {"ip": ip, "pool": pool, 'id': ip_id}},
            202
        )
        req_all = mock.MagicMock()
        req_all.get_response.return_value = resp
        resp_ass = fakes.create_fake_json_resp({}, 202)
        req_ass = mock.MagicMock()
        req_ass.get_response.return_value = resp_ass
        m_req.side_effect = [req_all,
                             req_ass]
        ret = self.helper.assign_floating_ip(None, net_id, device_id)
        self.assertIsNotNone(ret)
        self.assertEqual(net_id, ret['network_id'])
        self.assertEqual(device_id, ret['compute_id'])
        self.assertEqual(ip, ret['ip'])
        self.assertEqual(pool, ret['pool'])