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


import copy

from ooi import exception
from ooi.occi import helpers


def compare_schemes(expected_type, actual):
    actual_scheme, actual_term = helpers.decompose_type(actual)
    if expected_type.scheme != actual_scheme:
        return False
    try:
        if expected_type.term != actual_term:
            return False
    except AttributeError:
        # ignore the fact the type does not have a term
        pass
    return True


def validate(schema):
    def accepts(f):
        # TODO(enolfc): proper testing and attribute checking.
        def _validate(obj, req, body, *args, **kwargs):
            parsed_obj = req.parse()
            if "kind" in schema:
                try:
                    if schema["kind"].type_id != parsed_obj["kind"]:
                        raise exception.OCCISchemaMismatch(
                            expected=schema["kind"].type_id,
                            found=parsed_obj["kind"])
                except KeyError:
                    raise exception.OCCIMissingType(
                        type_id=schema["kind"].type_id)
            unmatched = copy.copy(parsed_obj["mixins"])
            for m in schema.get("mixins", []):
                for um in unmatched:
                    if compare_schemes(m, um):
                        unmatched[um] -= 1
                        break
                else:
                    raise exception.OCCIMissingType(type_id=m.scheme)
            for m in schema.get("optional_mixins", []):
                for um in unmatched:
                    if compare_schemes(m, um):
                        unmatched[um] -= 1
            unexpected = [m for m in unmatched if unmatched[m]]
            if unexpected:
                raise exception.OCCISchemaMismatch(expected="",
                                                   found=unexpected)
            return f(obj, parsed_obj, req, body, *args, **kwargs)
        return _validate
    return accepts
