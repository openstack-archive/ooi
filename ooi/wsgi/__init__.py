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

from oslo_log import log as logging
import routes
import routes.middleware
import webob.dec

from ooi import exception
from ooi.wsgi import serializers
from ooi.wsgi import utils

LOG = logging.getLogger(__name__)


class Request(webob.Request):
    def get_content_type(self):
        """Determine content type of the request body.

        Does not do any body introspection, only checks header

        """
        if "Content-Type" not in self.headers:
            return None

        content_type = self.content_type

        if not content_type or content_type == 'text/plain':
            return None

        if content_type not in serializers.get_supported_content_types():
            raise exception.InvalidContentType(content_type=content_type)

        return content_type

    def get_best_match_content_type(self):
        content_type = self.get_content_type()
        if content_type is None:
            content_types = serializers.get_supported_content_types()
            content_type = self.accept.best_match(content_types)
        return content_type


class OCCIMiddleware(object):
    @classmethod
    def factory(cls, global_conf, **local_conf):
        """Factory method for paste.deploy."""
        return cls

    def __init__(self, application):
        self.application = application

        self.resources = {}

        self.mapper = routes.Mapper()
        self._setup_routes()

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


            def create_resource():
                return ooi.wsgi.Resource(Controller())

        This method could populate the mapper as follows:

        .. code-block:: python

            self.resources["query"] = query.create_resource()
            self.mapper.connect("query", "/-/",
                                controller=self.resources["query"],
                                action="index")

        or if the Controller has all the CRUD operations:

        .. code-block:: python

            self.resources["resources"] = query.create_resource()
            self.mapper.resource("resource", "resources",
                                 controller=self.resources["resources"])

        """
        self.mapper.redirect("", "/")

    @webob.dec.wsgify(RequestClass=Request)
    def __call__(self, req):
        response = self.process_request(req)
        if response:
            return response

        response = req.get_response(self.application)
        return self.process_response(response)

    def process_request(self, req):
        match = self.mapper.match(req.path, req.environ)
        if not match:
            return webob.exc.HTTPNotFound()
        method = match["controller"]
        return method(req, match)

    def process_response(self, response):
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

    def get_body(self, request):
        try:
            content_type = request.get_content_type()
        except exception.InvalidContentType:
            LOG.debug("Unrecognized Content-Type provided in request")
            return None, ''

        return content_type, request.body

    @staticmethod
    def _should_have_body(request):
        return request.method in ("POST", "PUT")

    def __call__(self, request, args):
        """Control the method dispatch."""
        action_args = self.get_action_args(args)
        action = action_args.pop('action', None)
        try:
            accept = request.get_best_match_content_type()
        except exception.InvalidContentType:
            msg = "Unsupported Content-Type"
            return Fault(webob.exc.HTTPBadRequest(explanation=msg))

        content_type, body = self.get_body(request)

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
        if self._should_have_body(request):
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
        if not response:
            resp_obj = None
            # We got something
            if type(action_result) is list:
                resp_obj = ResponseObject(action_result)
            elif isinstance(action_result, ResponseObject):
                resp_obj = action_result
            else:
                response = action_result
            if resp_obj and not response:
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
            serializer = _serializer()

        response = webob.Response()
        response.status_int = self.code
        for hdr, value in self._headers.items():
            response.headers[hdr] = utils.utf8(value)
        response.headers['Content-Type'] = content_type
        if self.obj is not None:
            response.charset = 'utf8'
            response.body = serializer.serialize(self.obj)

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

        if isinstance(ex_value, exception.Invalid):
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

        # We didn't handle the exception
        return False


class Fault(webob.exc.HTTPException):
    """Wrap webob.exc.HTTPException to provide API friendly response."""

    _fault_names = {
        400: "badRequest",
        401: "unauthorized",
        403: "forbidden",
        404: "itemNotFound",
        405: "badMethod",
        409: "conflictingRequest",
        413: "overLimit",
        415: "badMediaType",
        429: "overLimit",
        501: "notImplemented",
        503: "serviceUnavailable"}

    def __init__(self, exception):
        """Create a Fault for the given webob.exc.exception."""
        self.wrapped_exc = exception
        for key, value in self.wrapped_exc.headers.items():
            self.wrapped_exc.headers[key] = str(value)
        self.status_int = exception.status_int

    @webob.dec.wsgify()
    def __call__(self, req):
        """Generate a WSGI response based on the exception passed to ctor."""

        # Replace the body with fault details.
        code = self.wrapped_exc.status_int
        fault_name = self._fault_names.get(code, "occiFault")
        explanation = self.wrapped_exc.explanation
        LOG.debug("Returning %(code)s to user: %(explanation)s",
                  {'code': code, 'explanation': explanation})

        fault_data = {
            fault_name: {
                'code': code,
                'message': explanation}}
        if code == 413 or code == 429:
            retry = self.wrapped_exc.headers.get('Retry-After', None)
            if retry:
                fault_data[fault_name]['retryAfter'] = retry

        content_type = req.content_type or "text/plain"
        mtype = serializers.get_media_map().get(content_type,
                                                "text")
        serializer = serializers.get_default_serializers()[mtype]
        self.wrapped_exc.body = serializer().serialize(fault_data)
        self.wrapped_exc.content_type = content_type

        return self.wrapped_exc

    def __str__(self):
        return self.wrapped_exc.__str__()
