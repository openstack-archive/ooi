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

from ooi.wsgi import utils


_MEDIA_TYPE_MAP = collections.OrderedDict([
    ('text/plain', 'text'),
    ('text/occi', 'header')
])


class TextSerializer(object):
    def serialize(self, data):
        if not isinstance(data, list):
            data = [data]

        ret = "\n".join([str(d) for d in data])
        return None, utils.utf8(ret)


class HeaderSerializer(object):
    def serialize(self, data):
        if not isinstance(data, list):
            data = [data]

        headers = []
        body = []
        for d in data:
            if hasattr(d, "headers"):
                headers.extend(d.headers())
            else:
                body.append(str(d))

        return headers, body


_SERIALIZERS_MAP = {
    "text": TextSerializer,
    "header": HeaderSerializer,
}


def get_media_map():
    return _MEDIA_TYPE_MAP


def get_default_serializers():
    return _SERIALIZERS_MAP


def get_supported_content_types():
    return _MEDIA_TYPE_MAP.keys()
