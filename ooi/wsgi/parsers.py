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


def _quoted_split(s, separator=',', quotes='"'):
    """Splits a string considering quotes.

    e.g. _quoted_split('a,"b,c",d') -> ['a', '"b,c"', 'd']
    """
    splits = []
    partial = []
    in_quote = None
    for c in s:
        if in_quote:
            if c == in_quote:
                in_quote = None
        else:
            if c in quotes:
                in_quote = c
        if not in_quote and c in separator:
            if partial:
                splits.append(''.join(partial))
            partial = []
        else:
            partial.append(c)
    if partial:
        splits.append(''.join(partial))
    return splits


def _split_unquote(s, separator="="):
    """Splits a string considering quotes and removing them in the result.

    e.g. _split_unquote('a="b=d"') -> ['a', 'b=d']
    """
    lex = shlex.shlex(s, posix=True)
    lex.commenters = ""
    lex.whitespace = separator
    lex.whitespace_split = True
    return list(lex)


class BaseParser(object):
    def __init__(self, headers, body):
        self.headers = headers
        self.body = body

    def parse(self):
        raise NotImplemented


class TextParser(BaseParser):
    def parse_categories(self, headers):
        kind = action = None
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        try:
            categories = headers["Category"]
        except KeyError:
            raise exception.OCCIInvalidSchema("No categories")
        for ctg in _quoted_split(categories):
            ll = _quoted_split(ctg, "; ")
            d = {"term": ll[0]}  # assumes 1st element => term's value
            try:
                d.update(dict([_split_unquote(i) for i in ll[1:]]))
            except ValueError:
                raise exception.OCCIInvalidSchema("Unable to parse category")
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
            for attr in _quoted_split(header_attrs):
                l = _split_unquote(attr)
                attrs[l[0].strip()] = l[1]
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
