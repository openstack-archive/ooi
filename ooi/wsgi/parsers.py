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
import shlex

from ooi import exception


_MEDIA_TYPE_MAP = collections.OrderedDict([
    ('text/plain', 'text'),
    ('text/occi', 'header')
])


class BaseParser(object):
    def __init__(self, headers, body):
        self.headers = headers
        self.body = body

    def parse(self):
        raise NotImplemented


def _lexize(s, separator, ignore_whitespace=False):
    lex = shlex.shlex(instream=s, posix=True)
    lex.commenters = ""
    if ignore_whitespace:
        lex.whitespace = separator
    else:
        lex.whitespace += separator
    lex.whitespace_split = True
    return list(lex)


def _lexise_header(s):
    return _lexize(s, separator=",", ignore_whitespace=True)


class TextParser(BaseParser):
    def parse_categories(self, headers):
        kind = action = None
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        try:
            categories = headers["Category"]
        except KeyError:
            raise exception.OCCIInvalidSchema("No categories")
        for ctg in _lexise_header(categories):
            ll = _lexize(ctg, ";")
            d = {"term": ll[0]}  # assumes 1st element => term's value
            d.update(dict([i.split('=') for i in ll[1:]]))
            ctg_class = d.get("class", None)
            ctg_type = '%(scheme)s%(term)s' % d
            if ctg_class == "kind":
                if kind is not None:
                    raise exception.OCCIInvalidSchema("Duplicated Kind")
                kind = ctg_type
            elif ctg_class == "action":
                if action is not None:
                    raise exception.OCCIInvalidSchema("Duplicated action")
                action = ctg_type
            elif ctg_class == "mixin":
                mixins[ctg_type] += 1
            schemes[d["scheme"]].append(d["term"])
        if action and kind:
            raise exception.OCCIInvalidSchema("Action and kind together?")
        return {
            "category": kind or action,
            "mixins": mixins,
            "schemes": schemes,
        }

    def parse_attributes(self, headers):
        attrs = {}
        try:
            header_attrs = headers["X-OCCI-Attribute"]
            for attr in _lexise_header(header_attrs):
                n, v = attr.split('=', 1)
                attrs[n.strip()] = v
        except KeyError:
            pass
        return attrs

    def _convert_to_headers(self):
        if not self.body:
            raise exception.OCCIInvalidSchema("No schema found")
        hdrs = collections.defaultdict(list)
        for l in self.body.splitlines():
            hdr, content = l.split(":", 1)
            hdrs[hdr].append(content)
        return {hdr: ','.join(hdrs[hdr]) for hdr in hdrs}

    def parse(self):
        body_headers = self._convert_to_headers()
        obj = self.parse_categories(body_headers)
        obj['attributes'] = self.parse_attributes(body_headers)
        return obj


class HeaderParser(TextParser):
    def parse(self):
        obj = self.parse_categories(self.headers)
        obj['attributes'] = self.parse_attributes(self.headers)
        return obj


_PARSERS_MAP = {
    "text": TextParser,
    "header": HeaderParser,
}


def get_media_map():
    return _MEDIA_TYPE_MAP


def get_default_parsers():
    return _PARSERS_MAP


def get_supported_content_types():
    return _MEDIA_TYPE_MAP.keys()
