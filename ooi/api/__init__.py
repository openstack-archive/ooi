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

import six.moves.urllib.parse as urlparse

from ooi import exception


def _lexize(s, separator, ignore_whitespace=False):
    lex = shlex.shlex(instream=s, posix=True)
    lex.commenters = ""
    if ignore_whitespace:
        lex.whitespace = separator
    else:
        lex.whitespace += separator
    lex.whitespace_split = True
    return list(lex)


def parse(f):
    def _parse(obj, req, *args, **kwargs):
        headers = {}
        try:
            l = []
            params = {}
            for ctg in _lexize(req.headers["Category"],
                               separator=',',
                               ignore_whitespace=True):
                ll = _lexize(ctg, ';')
                d = {"term": ll[0]}  # assumes 1st element => term's value
                d.update(dict([i.split('=') for i in ll[1:]]))
                l.append(d)
                params[urlparse.urlparse(d["scheme"]).path] = d["term"]
            headers["Category"] = l
        except KeyError:
            raise exception.HeaderNotFound(header="Category")

        return f(obj, req, headers, params, *args, **kwargs)
    return _parse


def _get_header_by_class(headers, class_id):
    return [h for h in headers["Category"] if h["class"] in [class_id]]


def validate(class_id, schemas, term=None):
    def accepts(f):
        def _validate(obj, req, headers, params, *args, **kwargs):
            """Category headers validation.

            Arguments::
                class_id:        type of OCCI class (kind, mixin, ..).
                schemas:         dict mapping the mandatory schemas with its
                                 occurrences.
                term (optional): if present, validates its value.

            Validation checks::
                class_presence:     asserts the existance of given class_id.
                scheme_occurrences: enforces the number of occurrences of the
                                    given schemas.
                term_validation:    asserts the correct term value of the
                                    matching headers.
            """
            header_l = _get_header_by_class(headers, class_id)

            def class_presence():
                if not header_l:
                    raise exception.OCCINoClassFound(class_id=class_id)

            def scheme_occurrences():
                d = collections.Counter([h["scheme"]
                                         for h in header_l])
                s = set(d.items()) ^ set(schemas.items())
                if len(s) != 0:
                    mismatched_schemas = [(scheme, d[scheme])
                                          for scheme in dict(s).keys()]
                    raise exception.OCCISchemaOccurrencesMismatch(
                        mismatched_schemas=mismatched_schemas)

            def term_validation():
                if [h for h in header_l if h["term"] not in [term]]:
                    raise exception.OCCINotCompliantTerm(term=term)

            class_presence()
            scheme_occurrences()
            if term:
                term_validation()

            return f(obj, req, headers, params, *args, **kwargs)
        return _validate
    return accepts
