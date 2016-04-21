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

import re

import routes
import routes.middleware
import webob.dec

import ooi.api.compute
import ooi.api.network
import ooi.api.network_link
from ooi.api import query
import ooi.api.storage
import ooi.api.storage_link
from ooi import config
from ooi import exception
from ooi.log import log as logging
from ooi import utils
from ooi import version
from ooi.wsgi import parsers
from ooi.wsgi import serializers

LOG = logging.getLogger(__name__)

occi_opts = [
    config.cfg.StrOpt('ooi_listen',
                      default="0.0.0.0",
                      help='The IP address on which the OCCI (ooi) API '
                      'will listen.'),
    config.cfg.IntOpt('ooi_listen_port',
                      default=8787,
                      help='The port on which the OCCI (ooi) API '
                      'will listen.'),
    config.cfg.IntOpt('ooi_workers',
                      help='Number of workers for OCCI (ooi) API service. '
                      'The default will be equal to the number of CPUs '
                      'available.'),
    # NEUTRON
    config.cfg.StrOpt('neutron_ooi_endpoint',
                      default="http://127.0.0.1:9696/v2.0",
                      help='Neutron end point which access to'
                           ' the Neutron Restful API.'),
]

CONF = config.cfg.CONF
CONF.register_opts(occi_opts)


class Request(webob.Request):
    def should_have_body(self):
        return self.method in ("POST", "PUT")

    def get_content_type(self):
        """Determine content type of the request body."""
        if not self.content_type:
            return None

        if not self.should_have_body():
            return None

        content_types = self.content_type.split(",")

        for ct in content_types:
            if ct in parsers.get_supported_content_types():
                return ct

        LOG.debug("Unrecognized Content-Type provided in request")
        raise exception.InvalidContentType(content_type=self.content_type)

    def get_best_match_content_type(self, default_match=None):
        content_types = serializers.get_supported_content_types()
        content_type = self.accept.best_match(content_types,
                                              default_match=default_match)
        if not content_type:
            LOG.debug("Unrecognized Accept Content-type provided in request")
            raise exception.InvalidAccept(content_type=self.accept)
        return content_type

    def get_parser(self):
        mtype = parsers.get_media_map().get(self.get_content_type(), "header")
        return parsers.get_default_parsers()[mtype]


class OCCIMiddleware(object):

    occi_version = "1.1"
    occi_string = "OCCI/%s" % occi_version

    @classmethod
    def factory(cls, global_conf, **local_conf):
        """Factory method for paste.deploy."""
        def _factory(app):
            conf = global_conf.copy()
            conf.update(local_conf)
            return cls(app, **local_conf)
        return _factory

    def __init__(self, application, openstack_version="/v2.1",
                 neutron_ooi_endpoint="http://127.0.0.1:9696/v2.0"):
        self.application = application
        self.openstack_version = openstack_version
        self.neutron_ooi_endpoint = neutron_ooi_endpoint
        self.resources = {}

        self.mapper = routes.Mapper()
        self._setup_routes()

    def _create_resource(self, controller, neutron_ooi_endpoint=None):
        if neutron_ooi_endpoint:
            return Resource(controller(self.neutron_ooi_endpoint))
        else:
            return Resource(controller(self.application,
                                       self.openstack_version))

    def _setup_resource_routes(self, resource, controller):
        path = "/" + resource
        # These two could be removed for total OCCI compliance
        self.mapper.connect(resource, path, controller=controller,
                            action="index", conditions=dict(method=["GET"]))
        self.mapper.connect(resource, path, controller=controller,
                            action="create", conditions=dict(method=["POST"]))
        # OCCI states that paths must end with a "/" when operating on pahts,
        # that are not location pahts or resource instances
        self.mapper.connect(resource, path + "/", controller=controller,
                            action="index", conditions=dict(method=["GET"]))
        self.mapper.connect(resource, path + "/", controller=controller,
                            action="create", conditions=dict(method=["POST"]))
        self.mapper.connect(resource, path + "/{id}", controller=controller,
                            action="update", conditions=dict(method=["PUT"]))
        self.mapper.connect(resource, path + "/{id}", controller=controller,
                            action="delete",
                            conditions=dict(method=["DELETE"]))
        self.mapper.connect(resource, path + "/{id}", controller=controller,
                            action="show", conditions=dict(method=["GET"]))
        # OCCI specific, delete all resources
        self.mapper.connect(path + "/", controller=controller,
                            action="delete_all",
                            conditions=dict(method=["DELETE"]))
        # Actions
        self.mapper.connect(path + "/{id}", controller=controller,
                            action="run_action",
                            conditions=dict(method=["POST"]))

    def _setup_routes(self):
        """Setup the mapper routes.

        This method should populate the mapper with the Resources
        for each of the Controllers.

        For example, if ooi.api.query contains the following:

        .. code-block:: python

            class Controller(object):
                def index(self, *args, **kwargs):
                    # Currently we do not have anything to do here
                    return None

        This method could populate the mapper as follows:

        .. code-block:: python

            self.resources["query"] = self._create_resource(query.Controller)
            self.mapper.connect("query", "/-/",
                                controller=self.resources["query"],
                                action="index")

        or if the Controller has all the CRUD operations:

        .. code-block:: python

            self.resources["servers"] = self._create_resource(query.Controller)
            self.mapper.resource("server", "servers",
                                 controller=self.resources["servers"])

        """
        self.mapper.redirect("", "/")

        self.resources["query"] = self._create_resource(query.Controller)
        self.mapper.connect("query", "/-/",
                            controller=self.resources["query"],
                            action="index")
        # RFC5785, OCCI section 3.6.7
        self.mapper.connect("query", "/.well-known/org/ogf/occi/-/",
                            controller=self.resources["query"],
                            action="index")

        self.resources["compute"] = self._create_resource(
            ooi.api.compute.Controller)
        self._setup_resource_routes("compute", self.resources["compute"])

        self.resources["storage"] = self._create_resource(
            ooi.api.storage.Controller)
        self._setup_resource_routes("storage", self.resources["storage"])

        self.resources["storagelink"] = self._create_resource(
            ooi.api.storage_link.Controller)
        self._setup_resource_routes("storagelink",
                                    self.resources["storagelink"])

        self.resources["networklink"] = self._create_resource(
            ooi.api.network_link.Controller)
        self._setup_resource_routes("networklink",
                                    self.resources["networklink"])

        self.resources["network"] = self._create_resource(
            ooi.api.network.Controller, self.neutron_ooi_endpoint)
        self._setup_resource_routes("network",
                                    self.resources["network"])

    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        response = self.process_request(req)
        if not response:
            response = req.get_response(self.application)

        return self.process_response(response)

    def process_request(self, req):
        if req.user_agent:
            # FIXME(aloga): review the regexp, since it will only match the
            # first string
            match = re.search(r"\bOCCI/\d\.\d\b", req.user_agent)
            if match and self.occi_string != match.group():
                return Fault(webob.exc.HTTPNotImplemented(
                             explanation="%s not supported" % match.group()))

        match = self.mapper.match(req.path_info, req.environ)
        if not match:
            return Fault(webob.exc.HTTPNotFound())
        method = match["controller"]
        return method(req, match)

    def process_response(self, response):
        """Process a response by adding our headers."""
        server_string = "ooi/%s %s" % (version.version_string,
                                       self.occi_string)

        headers = (("server", server_string),)
        if isinstance(response, Fault):
            for key, val in headers:
                response.wrapped_exc.headers.add(key, val)
        else:
            for key, val in headers:
                response.headers.add(key, val)
        return response


class Resource(object):
    def __init__(self, controller):
        self.controller = controller
        self.default_serializers = serializers.get_default_serializers()

    def get_action_args(self, args):
        """Parse dictionary created by routes library."""
        try:
            del args['controller']
        except KeyError:
            pass

        try:
            del args['format']
        except KeyError:
            pass

        return args

    def __call__(self, request, args):
        """Control the method dispatch."""
        action_args = self.get_action_args(args)
        action = action_args.pop('action', None)
        try:
            accept = request.get_best_match_content_type()
            content_type = request.get_content_type()
        except exception.InvalidContentType as e:
            msg = e.format_message()
            return Fault(webob.exc.HTTPNotAcceptable(explanation=msg))

        body = request.body

        # Get the implementing method
        try:
            method = self.get_method(request, action,
                                     content_type, body)
        except (AttributeError, TypeError):
            return Fault(webob.exc.HTTPNotFound())
        except KeyError as ex:
            msg = "There is no such action: %s" % ex.args[0]
            return Fault(webob.exc.HTTPBadRequest(explanation=msg))

        contents = {}
        if request.should_have_body():
            # allow empty body with PUT and POST
            if request.content_length == 0:
                contents = {'body': None}
            else:
                contents["body"] = body

        action_args.update(contents)

        response = None
        try:
            with ResourceExceptionHandler():
                action_result = self.dispatch(method, request, action_args)
        except Fault as ex:
            response = ex

        # No exceptions, so create a response
        # NOTE(aloga): if the middleware returns None, the pipeline will
        # continue, but we do not want to do so, so we convert the action
        # result to a ResponseObject.
        if not response:
            if isinstance(action_result, ResponseObject):
                resp_obj = action_result
            else:
                resp_obj = ResponseObject(action_result)

            response = resp_obj.serialize(request, accept,
                                          self.default_serializers)
        return response

    def get_method(self, request, action, content_type, body):
        """Look up the action-specific method and its extensions."""

        if not self.controller:
            meth = getattr(self, action)
        else:
            meth = getattr(self.controller, action)

        return meth

    def dispatch(self, method, request, action_args):
        """Dispatch a call to the action-specific method."""
        return method(req=request, **action_args)


class ResponseObject(object):
    def __init__(self, obj, code=None, headers=None, **serializers):
        self.obj = obj
        self.serializers = serializers
        self._default_code = 200
        self._code = code
        self._headers = headers or {}
        self.serializer = None
        self.media_type = None

    def get_serializer(self, content_type, default_serializers=None):
        """Returns the serializer for the wrapped object.

        Returns the serializer for the wrapped object subject to the
        indicated content type.  If no serializer matching the content
        type is attached, an appropriate serializer drawn from the
        default serializers will be used.  If no appropriate
        serializer is available, raises InvalidContentType.
        """

        default_serializers = default_serializers or {}
        try:
            if content_type is None:
                content_type = "text/plain"

            mtype = serializers.get_media_map().get(content_type,
                                                    content_type)
            if mtype in self.serializers:
                return mtype, self.serializers[mtype]
            else:
                return mtype, default_serializers[mtype]
        except (KeyError, TypeError):
            raise exception.InvalidContentType(content_type=content_type)

    def serialize(self, request, content_type, default_serializers=None):
        if self.serializer:
            serializer = self.serializer
        else:
            _mtype, _serializer = self.get_serializer(content_type,
                                                      default_serializers)
            env = {"application_url": request.application_url + "/"}
            serializer = _serializer(env)

        response = webob.Response()
        response.status_int = self.code
        for hdr, value in self._headers.items():
            response.headers[hdr] = utils.utf8(value)
        response.headers['Content-Type'] = content_type
        response.charset = 'utf8'
        if self.obj is not None:
            headers, body = serializer.serialize(self.obj)
            if headers is not None:
                for hdr in headers:
                    response.headers.add(*hdr)
            if body:
                response.body = body

            # 204 should be used if there is no content
            if (not (headers or body) and
                    response.status_int in [200, 201, 202]):
                response.status_int = 204

        return response

    @property
    def code(self):
        """Retrieve the response status."""

        return self._code or self._default_code

    @property
    def headers(self):
        """Retrieve the headers."""

        return self._headers.copy()


class ResourceExceptionHandler(object):
    """Context manager to handle Resource exceptions.

    Used when processing exceptions generated by API implementation
    methods (or their extensions).  Converts most exceptions to Fault
    exceptions, with the appropriate logging.
    """

    def __enter__(self):
        return None

    def __exit__(self, ex_type, ex_value, ex_traceback):
        if not ex_value:
            return True

        if isinstance(ex_value, exception.OCCIException):
            raise Fault(exception.ConvertedException(
                        code=ex_value.code,
                        explanation=ex_value.format_message()))
        elif isinstance(ex_value, exception.NotImplemented):
            raise Fault(exception.ConvertedException(
                        code=ex_value.code,
                        explanation=ex_value.format_message()))
        elif isinstance(ex_value, TypeError):
            exc_info = (ex_type, ex_value, ex_traceback)
            LOG.error('Exception handling resource: %s', ex_value,
                      exc_info=exc_info)
            raise Fault(webob.exc.HTTPBadRequest())
        elif isinstance(ex_value, Fault):
            LOG.info("Fault thrown: %s", ex_value)
            raise ex_value
        elif isinstance(ex_value, webob.exc.HTTPException):
            LOG.info("HTTP exception thrown: %s", ex_value)
            raise Fault(ex_value)
        else:
            LOG.exception("Unexpected exception: %s" % ex_value)
            raise Fault(webob.exc.HTTPInternalServerError())

        # We didn't handle the exception
        return False


class Fault(webob.exc.HTTPException):
    """Wrap webob.exc.HTTPException to provide API friendly response."""

    def __init__(self, exception):
        """Create a Fault for the given webob.exc.exception."""
        self.wrapped_exc = exception
        for key, value in self.wrapped_exc.headers.items():
            self.wrapped_exc.headers[key] = str(value)
        self.status_int = exception.status_int

    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        """Generate a WSGI response based on the exception passed to ctor."""

        # Replace the body with fault details.
        code = self.wrapped_exc.status_int
        explanation = self.wrapped_exc.explanation
        LOG.debug("Returning %(code)s to user: %(explanation)s",
                  {'code': code, 'explanation': explanation})

        def_ct = "text/plain"
        content_type = req.get_best_match_content_type(default_match=def_ct)
        mtype = serializers.get_media_map().get(content_type,
                                                "text")
        serializer = serializers.get_default_serializers()[mtype]
        env = {}
        serialized_exc = serializer(env).serialize(self.wrapped_exc)
        self.wrapped_exc.content_type = content_type
        self.wrapped_exc.body = serialized_exc[1]

        # We need to specify the HEAD req.method here to be HEAD because of the
        # way that webob.exc.WSGIHTTPException.__call__ generates the response.
        # The text/occi will not have a body since it is based on headers. We
        # cannot set this earlier in the middleware, since we are calling
        # OpenStack and it will fail because the responses won't contain a
        # body.
        if content_type == "text/occi":
            req.method = "HEAD"

        return self.wrapped_exc

    def __str__(self):
        return self.wrapped_exc.__str__()
