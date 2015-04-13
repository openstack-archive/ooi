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
    #    ('text/plain', 'text'),
    ('text/occi', 'header')
])


def _lexize(s, separator, ignore_whitespace=False):
    lex = shlex.shlex(instream=s, posix=True)
    lex.commenters = ""
    if ignore_whitespace:
        lex.whitespace = separator
    else:
        lex.whitespace += separator
    lex.whitespace_split = True
    return list(lex)


class BaseParser(object):
    def validate(self):
        return False


class TextParser(BaseParser):
    pass


class HeaderParser(BaseParser):
    def parse_categories(self, headers, body):
        kind = None
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        try:
            categories = headers["Category"]
        except KeyError:
            raise exception.OCCIInvalidSchema("No categories")
        for ctg in _lexize(categories, separator=",", ignore_whitespace=True):
            ll = _lexize(ctg, ";")
            d = {"term": ll[0]}  # assumes 1st element => term's value
            d.update(dict([i.split('=') for i in ll[1:]]))
            ctg_class = d.get("class", None)
            ctg_type = '%(scheme)s%(term)s' % d
            if ctg_class == "kind":
                if kind is not None:
                    raise exception.OCCIInvalidSchema("Duplicated Kind")
                kind = ctg_type
            elif ctg_class == "mixin":
                mixins[ctg_type] += 1
            schemes[d["scheme"]].append(d["term"])
        return {
            "kind": kind,
            "mixins": mixins,
            "schemes": schemes,
        }

    def parse_attributes(self, headers, body):
        attrs = {}
        try:
            header_attrs = headers["X-OCCI-Attribute"]
            for attr in _lexize(header_attrs, separator=",",
                                ignore_whitespace=True):
                n, v = attr.split('=', 1)
                attrs[n.strip()] = v
        except KeyError:
            pass
        return attrs

    def parse(self, headers, body):
        obj = self.parse_categories(headers, body)
        obj['attributes'] = self.parse_attributes(headers, body)
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
