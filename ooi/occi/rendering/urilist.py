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

from ooi.occi.core import collection
from ooi.occi.rendering import headers
from ooi.occi.rendering import text
from ooi import utils


class LocationRenderer(object):
    def __init__(self, obj):
        self.obj = obj

    def render(self, env={}):
        app_url = env.get("application_url", "")
        return utils.join_url(app_url, self.obj.location)


class CollectionRenderer(headers.CollectionRenderer):
    def render(self, env={}):
        hdr = super(CollectionRenderer, self).render(env)
        return "\n".join([l[1] for l in hdr])


def get_renderer(obj):
    """Get the correct renderer for the given object."""
    if isinstance(obj, webob.exc.HTTPException):
        return text.ExceptionRenderer(obj)
    elif isinstance(obj, collection.Collection):
        return CollectionRenderer(obj)
    elif getattr(obj, 'location', None):
        return LocationRenderer(obj)
    else:
        return text.ExceptionRenderer(obj)
