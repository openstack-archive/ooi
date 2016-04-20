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

import six
import six.moves.urllib.parse as urlparse


def utf8(value):
    """Try to turn a string into utf-8 if possible.

    Code is modified from the utf8 function in
    http://github.com/facebook/tornado/blob/master/tornado/escape.py

    """
    if isinstance(value, six.text_type):
        return value.encode('utf-8')
    assert isinstance(value, str)
    return value


def join_url(base, parts):
    """Join several parts into a url.

    :param base: the base url
    :parts: parts to join into the url
    """
    url = base
    if not isinstance(parts, (list, tuple)):
        parts = [parts]

    for p in parts:
        if p.startswith("/"):
            # We won't get an absolute url
            p = p[1:]
        url = urlparse.urljoin(url, p)
    return url


def make_body(resource, parameters):
    """Creates body request using the parameters.

    :param resource: kind of resource
    :param parameters: list of parameters
    """
    content = {}
    for key in parameters.keys():
        content[key] = parameters[key]
    if resource:
        body = {resource: content}
    else:
        body = content
    return body


def get_query_string(parameters):
    """Creates query string.

    :param parameters: list of parameters
    """
    if parameters is None:
        query_string = None
    else:
        query_string = urlparse.urlencode(parameters)
    return query_string


def translate_parameters(translation, parameters):
    """Translates parameter names to OS

    :param translation: list of names for translation
    :param parameters: list of parameters
    """
    if not parameters:
        return None
    out = {}
    for key in parameters.keys():
        if key in translation:
            out[translation[key]] = parameters[key]
    return out
