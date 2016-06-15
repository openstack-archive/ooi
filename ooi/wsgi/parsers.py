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
import copy
import json
import shlex

from six.moves import urllib

from ooi import exception


_MEDIA_TYPE_MAP = collections.OrderedDict([
    ('text/plain', 'text'),
    ('text/occi', 'header'),
    ('application/occi+json', 'json'),
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

    def parse_attribute_value(self, value):
        v = value.strip()
        # quoted: string or bool
        if v[0] == '"':
            v = v.strip('"')
            if v == "true":
                return True
            elif v == "false":
                return False
            else:
                return v
        # unquoted: number or enum-val
        try:
            return int(v)
        except ValueError:
            try:
                return float(v)
            except ValueError:
                return v

    def parse_attributes(self, headers):
        attrs = {}
        try:
            header_attrs = headers["X-OCCI-Attribute"]
            for attr in _quoted_split(header_attrs):
                try:
                    n, v = attr.split("=", 1)
                    attrs[n.strip()] = self.parse_attribute_value(v)
                except ValueError:
                    raise exception.OCCIInvalidSchema("Unable to parse")
        except KeyError:
            pass
        return attrs

    def parse_links(self, headers):
        links = collections.defaultdict(list)
        try:
            header_links = headers["Link"]
        except KeyError:
            return links
        for link in _quoted_split(header_links):
            ll = _quoted_split(link, "; ")
            # remove the "<" and ">"
            if ll[0][1] != "<" and ll[0][-1] != ">":
                raise exception.OCCIInvalidSchema("Unable to parse link")
            link_id = ll[0][1:-1]
            target_location = None
            target_kind = None
            attrs = {}
            try:
                for attr in ll[1:]:
                    n, v = attr.split("=", 1)
                    n = n.strip().strip('"')
                    v = self.parse_attribute_value(v)
                    if n == "rel":
                        target_kind = v
                        continue
                    elif n == "occi.core.target":
                        target_location = v
                        continue
                    attrs[n] = v
            except ValueError:
                raise exception.OCCIInvalidSchema("Unable to parse link")
            if not (target_kind and target_location):
                raise exception.OCCIInvalidSchema("Unable to parse link")
            links[target_kind].append({
                "target": target_location,
                "attributes": attrs,
                "id": link_id,
            })
        return links

    def _convert_to_headers(self):
        if not self.body:
            raise exception.OCCIInvalidSchema("No schema found")
        hdrs = collections.defaultdict(list)
        for l in self.body.splitlines():
            hdr, content = l.split(":", 1)
            hdrs[hdr].append(content)
        return {hdr: ','.join(hdrs[hdr]) for hdr in hdrs}

    def _parse(self, headers):
        obj = self.parse_categories(headers)
        obj['attributes'] = self.parse_attributes(headers)
        obj['links'] = self.parse_links(headers)
        return obj

    def parse(self):
        return self._parse(self._convert_to_headers())


class HeaderParser(TextParser):
    def parse(self):
        return self._parse(self.headers)


class JsonParser(BaseParser):
    def parse_categories(self, obj):
        kind = action = None
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        if "kind" in obj:
            sch, term = urllib.parse.urldefrag(obj["kind"])
            schemes[sch + "#"].append(term)
            kind = obj["kind"]
            for m in obj.get("mixins", []):
                mixins[m] += 1
                sch, term = urllib.parse.urldefrag(m)
                schemes[sch + "#"].append(term)
        if "action" in obj:
            action = obj["action"]
            sch, term = urllib.parse.urldefrag(obj["action"])
            schemes[sch + "#"].append(term)
        if action and kind:
            raise exception.OCCIInvalidSchema("Action and kind together?")
        return {
            "category": kind or action,
            "mixins": mixins,
            "schemes": schemes,
        }

    def parse_attributes(self, obj):
        if "attributes" in obj:
            return copy.copy(obj["attributes"])
        return {}

    def parse_links(self, obj):
        links = collections.defaultdict(list)
        for l in obj.get("links", []):
            try:
                d = {
                    "target": l["target"]["location"],
                    "attributes": copy.copy(l.get("attributes", {})),
                }
                if "id" in l:
                    d["id"] = l["id"]
                links[l["target"]["kind"]].append(d)
            except KeyError:
                raise exception.OCCIInvalidSchema("Unable to parse link")
        return links

    def parse(self):
        try:
            obj = json.loads(self.body or "")
        except ValueError:
            raise exception.OCCIInvalidSchema("Unable to parse JSON")
        r = self.parse_categories(obj)
        r['attributes'] = self.parse_attributes(obj)
        r['links'] = self.parse_links(obj)
        return r


_PARSERS_MAP = {
    "text": TextParser,
    "header": HeaderParser,
    "json": JsonParser,
}


def get_media_map():
    return _MEDIA_TYPE_MAP


def get_default_parsers():
    return _PARSERS_MAP


def get_supported_content_types():
    return _MEDIA_TYPE_MAP.keys()
