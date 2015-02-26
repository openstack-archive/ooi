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

from ooi.occi.core import attribute
from ooi.occi import helpers


class Category(object):
    """OCCI Category."""

    def __init__(self, scheme, term, title, attributes=[], location=None):
        self._scheme = scheme
        self._term = term
        self._title = title

        helpers.check_type(attributes, attribute.Attribute)

        self._attributes = dict([(a.name, a) for a in attributes])
        self._location = location

    @property
    def scheme(self):
        return self._scheme

    @property
    def term(self):
        return self._term

    @property
    def title(self):
        return self._title

    @property
    def attributes(self):
        return self._attributes

    @property
    def location(self):
        return self._location
