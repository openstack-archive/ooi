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

from ooi.occi.rendering import headers


class TextRenderer(object):
    """Render OCCI objects into text.

    The text rendering is just the representation of the OCCI HTTP headers into
    text plain, so this renderer wraps around the actual header renderer and
    converts the headers into text.
    """
    def __init__(self, renderer):
        self.renderer = renderer

    def render(self, *args, **kwargs):
        """Render the OCCI object into text."""
        hdrs = self.renderer.render(*args, **kwargs)
        result = []
        for hdr in hdrs:
            result.append("%s: %s" % hdr)
        return "\n".join(result)


class ExceptionRenderer(object):
    def __init__(self, obj):
        self.obj = obj

    def render(self, *args, **kwargs):
        return self.obj.explanation


def get_renderer(obj):
    """Get the correct renderer for the given object."""
    if isinstance(obj, webob.exc.HTTPException):
        return ExceptionRenderer(obj)
    else:
        return TextRenderer(headers.get_renderer(obj))
