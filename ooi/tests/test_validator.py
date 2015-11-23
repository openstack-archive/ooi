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

import mock

from ooi import exception
from ooi.occi import validator
from ooi.tests import base


class TestValidator(base.TestCase):
    def test_category(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
        }
        cat = mock.MagicMock()
        cat.type_id = "foo type"

        scheme = {"category": cat}

        v = validator.Validator(pobj)
        self.assertTrue(v.validate(scheme))

    def test_category_missmatch(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        pobj = {
            "kind": "compute",
            "category": "foo bar baz",
            "mixins": mixins,
            "schemes": schemes,
        }
        cat = mock.MagicMock()
        cat.type_id = "foo type"

        scheme = {"category": cat}

        v = validator.Validator(pobj)
        self.assertRaises(exception.OCCISchemaMismatch, v.validate, scheme)

    def test_missing_category(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        pobj = {
            "kind": "compute",
            "mixins": mixins,
            "schemes": schemes,
        }
        cat = mock.MagicMock()
        cat.type_id = "foo type"

        scheme = {"category": cat}

        v = validator.Validator(pobj)
        self.assertRaises(exception.OCCIMissingType, v.validate, scheme)

    def test_mixins(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        mixins["http://example.com/scheme#foo"] += 1
        schemes["http://example.com/scheme#"].append("foo")
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
        }

        mixin = mock.MagicMock()
        scheme = {"mixins": [mixin]}

        mixin.scheme = "http://example.com/scheme#"
        mixin.term = "foo"
        v = validator.Validator(pobj)
        self.assertTrue(v.validate(scheme))

    def test_optional_mixins(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        mixins["http://example.com/scheme#foo"] += 1
        schemes["http://example.com/scheme#"].append("foo")
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
        }

        mixin = mock.MagicMock()
        mixin.scheme = "http://example.com/scheme#"
        mixin.term = "foo"
        scheme = {"optional_mixins": [mixin]}

        v = validator.Validator(pobj)
        self.assertTrue(v.validate(scheme))

    def test_mixin_schema_mismatch(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        mixins["http://example.com/scheme#foo"] += 1
        schemes["http://example.com/scheme#"].append("foo")
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
        }

        mixin = mock.MagicMock()
        mixin.scheme = "http://example.com/foo#"
        mixin.term = "foo"
        scheme = {"mixins": [mixin]}

        v = validator.Validator(pobj)
        self.assertRaises(exception.OCCIMissingType, v.validate, scheme)

    def test_mixin_schema_mismatch_term(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        mixins["http://example.com/scheme#foo"] += 1
        schemes["http://example.com/scheme#"].append("foo")
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
        }

        mixin = mock.MagicMock()
        mixin.scheme = "http://example.com/scheme#"
        mixin.term = "bar"
        scheme = {"mixins": [mixin]}

        v = validator.Validator(pobj)
        self.assertRaises(exception.OCCIMissingType, v.validate, scheme)

    def test_no_optional_mixins(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
        }

        mixin = mock.MagicMock()
        mixin.scheme = "http://example.com/scheme#"
        mixin.term = "foo"
        scheme = {"optional_mixins": [mixin]}

        v = validator.Validator(pobj)
        self.assertTrue(v.validate(scheme))

    def test_something_unexpected(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        mixins["http://example.com/scheme#foo"] += 1
        schemes["http://example.com/scheme#"].append("foo")
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
        }

        v = validator.Validator(pobj)
        self.assertRaises(exception.OCCISchemaMismatch, v.validate, {})

    def test_optional_links(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        links = {"foo": {"rel": "http://example.com/scheme#foo"}}
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
            "links": links
        }
        link = mock.MagicMock()
        link.type_id = "http://example.com/scheme#foo"
        scheme = {"optional_links": [link]}
        v = validator.Validator(pobj)
        self.assertTrue(v.validate(scheme))

    def test_optional_links_invalid(self):
        mixins = collections.Counter()
        schemes = collections.defaultdict(list)
        links = {"foo": {"rel": "http://example.com/scheme#foo"}}
        pobj = {
            "kind": "compute",
            "category": "foo type",
            "mixins": mixins,
            "schemes": schemes,
            "links": links
        }
        link = mock.MagicMock()
        link.type_id = "http://example.com/scheme#foo"
        scheme = {"optional_links": []}
        v = validator.Validator(pobj)
        self.assertRaises(exception.OCCISchemaMismatch, v.validate, scheme)
