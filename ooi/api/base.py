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

import abc
import copy

from ooi.api import helpers
from ooi import utils

from oslo_log import log as logging
import six
import webob.exc

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class Controller(object):
    def __init__(self, app, openstack_version):
        self.app = app
        self.openstack_version = openstack_version

    # FIXME(aloga): remove when refactor is finished
    def _get_req(self, req,
                 path=None,
                 content_type="application/json",
                 body=None,
                 method=None,
                 query_string=""):
        """Return a new Request object to interact with OpenStack.

        This method will create a new request starting with the same WSGI
        environment as the original request, prepared to interact with
        OpenStack. Namely, it will override the script name to match the
        OpenStack version. It will also override the path, content_type and
        body of the request, if any of those keyword arguments are passed.

        :param req: the original request
        :param path: new path for the request
        :param content_type: new content type for the request, defaults to
                             "application/json" if not specified
        :param body: new body for the request
        :param query_string: query string for the request, defaults to an empty
                             query if not specified
        :returns: a Request object
        """
        new_req = webob.Request(copy.copy(req.environ))
        new_req.script_name = self.openstack_version
        new_req.query_string = query_string
        if path is not None:
            new_req.path_info = path
        if content_type is not None:
            new_req.content_type = content_type
        if body is not None:
            new_req.body = utils.utf8(body)
        if method is not None:
            new_req.method = method
        return new_req

    # FIXME(aloga): remove when refactor is finished
    @staticmethod
    def get_from_response(response, element, default):
        return helpers.BaseHelper.get_from_response(response, element, default)
