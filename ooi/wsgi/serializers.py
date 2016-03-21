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

import collections

from ooi.occi.rendering import headers as header_rendering
from ooi.occi.rendering import text as text_rendering
from ooi.occi.rendering import urilist as urilist_rendering
from ooi import utils


_MEDIA_TYPE_MAP = collections.OrderedDict([
    ('text/plain', 'text'),
    ('text/occi', 'header'),
    ('text/uri-list', 'uri-list')

])


class BaseSerializer(object):
    def __init__(self, env):
        self.env = env


class TextSerializer(BaseSerializer):
    def serialize(self, data):
        if not isinstance(data, list):
            data = [data]

        renderers = []
        for d in data:
            renderers.append(text_rendering.get_renderer(d))

        ret = "\n".join([r.render(env=self.env) for r in renderers])
        return None, utils.utf8(ret)


class HeaderSerializer(BaseSerializer):
    def serialize(self, data):
        if not isinstance(data, list):
            data = [data]

        renderers = []
        for d in data:
            renderers.append(header_rendering.get_renderer(d))

        # Header renderers will return a list, so we must flatten the results
        # before returning them
        headers = [i for r in renderers for i in r.render(env=self.env)]
        return headers, utils.utf8("")


class UriListSerializer(TextSerializer):
    # TODO(enolfc): this is mostly duplicated code.
    def serialize(self, data):
        if not isinstance(data, list):
            data = [data]

        renderers = []
        for d in data:
            renderers.append(urilist_rendering.get_renderer(d))

        ret = "\n".join([r.render(env=self.env) for r in renderers])
        return None, utils.utf8(ret)


_SERIALIZERS_MAP = {
    "text": TextSerializer,
    "header": HeaderSerializer,
    "uri-list": UriListSerializer,
}


def get_media_map():
    return _MEDIA_TYPE_MAP


def get_default_serializers():
    return _SERIALIZERS_MAP


def get_supported_content_types():
    return _MEDIA_TYPE_MAP.keys()
