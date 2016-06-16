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


class Validator(object):
    def __init__(self, obj):
        self.parsed_obj = obj

    def _validate_category(self, category):
        try:
            if category.type_id != self.parsed_obj["category"]:
                raise exception.OCCISchemaMismatch(
                    expected=category.type_id,
                    found=self.parsed_obj["category"]
                )
        except KeyError:
            raise exception.OCCIMissingType(
                type_id=category.type_id)

    def _compare_schemes(self, expected_type, actual):
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

    def _validate_mandatory_mixins(self, mixins, unmatched):
        for m in mixins:
            for um in unmatched:
                if self._compare_schemes(m, um):
                    unmatched[um] -= 1
                    break
            else:
                # NOTE(aloga): I am not sure of this...
                expected = m.scheme
                if hasattr(m, "term"):
                    expected += m.term
                raise exception.OCCIMissingType(type_id=expected)
        return unmatched

    def _validate_optional_mixins(self, mixins, unmatched):
        for m in mixins:
            for um in unmatched:
                if self._compare_schemes(m, um):
                    unmatched[um] -= 1
                    break
        return unmatched

    def _validate_optional_links(self, expected, links):
        for uri, l in links.items():
            try:
                rel = l['rel']
            except KeyError:
                raise exception.OCCIMissingType(type_id=uri)
            for ex in expected:
                if rel == ex.type_id:
                    break
            else:
                expected_types = ', '.join([e.type_id for e in expected])
                raise exception.OCCISchemaMismatch(expected=expected_types,
                                                   found=l['rel'])

    def validate_attributes(self, required):
        """Validate required attributes

        :param required: required attributes
        """
        attr = self.parsed_obj.get("attributes", {})
        if required:
            for at in required:
                if at not in attr:
                    raise exception.Invalid(
                        "Expecting %s attribute" % at
                    )

    def validate(self, schema):
        if "category" in schema:
            self._validate_category(schema["category"])
        unmatched = copy.copy(self.parsed_obj["mixins"])
        unmatched = self._validate_mandatory_mixins(
            schema.get("mixins", []), unmatched)
        unmatched = self._validate_optional_mixins(
            schema.get("optional_mixins", []), unmatched)
        unexpected = [m for m in unmatched if unmatched[m]]
        if unexpected:
            raise exception.OCCISchemaMismatch(expected="",
                                               found=unexpected)
        self._validate_optional_links(
            schema.get("optional_links", []),
            self.parsed_obj.get("links", {}))
        return True
