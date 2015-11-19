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

import webob.exc

from ooi.log import log as logging

LOG = logging.getLogger(__name__)


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=0, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()


class OCCIException(Exception):
    """Base Nova Exception

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That msg_fmt will get printf'd
    with the keyword arguments provided to the constructor.

    """
    msg_fmt = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.msg_fmt % kwargs

            except Exception:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception('Exception in string format operation')
                for name, value in kwargs.iteritems():
                    LOG.error("%s: %s" % (name, value))    # noqa

                message = self.msg_fmt

        super(OCCIException, self).__init__(message)

    def format_message(self):
        # NOTE(mrodden): use the first argument to the python Exception object
        # which should be our full NovaException message, (see __init__)
        return self.args[0]


class Invalid(OCCIException):
    msg_fmt = "Unacceptable parameters."
    code = 400


class InvalidAction(Invalid):
    msg_fmt = "Invalid action %(action)s provided."


class InvalidContentType(Invalid):
    msg_fmt = "Invalid Content-type %(content_type)s."
    code = 406


class NoContentType(InvalidContentType):
    msg_fmt = "No Content-type provided."


class InvalidAccept(InvalidContentType):
    msg_fmt = "Invalid Accept %(content_type)s."


class NotImplemented(OCCIException):
    msg_fmt = "Action not implemented."
    code = 501


class OCCIInvalidSchema(Invalid):
    msg_fmt = "Found invalid schema: '%(msg)s'."


class OCCIMissingType(Invalid):
    msg_fmt = "Missing OCCI types: '%(type_id)s'."


class OCCISchemaMismatch(Invalid):
    msg_fmt = ("Schema does not match. Expecting '%(expected)s', "
               "but found '%(found)s'.")


class NotFound(OCCIException):
    msg_fmt = "Not Found"
    code = 404


class LinkNotFound(NotFound):
    msg_fmt = "Link Not Found: '%(link_id)s"


class ResourceNotFound(NotFound):
    msg_fmt = "Resource Not Found: '%(resource_id)s'"


class NetworkNotFound(NotFound):
    msg_fmt = "Network Resource Not Found: '%(resource_id)s'"


class NetworkPoolFound(NotFound):
    msg_fmt = "Network Pool Not Found: '%(pool)s'"


class MissingKeypairName(Invalid):
    msg_fmt = "Missing Keypair Name"
    code = 400
