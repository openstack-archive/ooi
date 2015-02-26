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

import abc

import six

from ooi.occi import helpers
from ooi.occi.core import attribute
from ooi.occi.core import kind
from ooi.occi.core import mixin


@six.add_metaclass(abc.ABCMeta)
class Entity(object):
    """OCCI Entity.

    Entity is an abstract type, which both Resource and Link inherit. Each
    sub-type of Entity is identified by a unique Kind instance
    """

    def __init__(self, id, title, mixins):
        helpers.check_type(mixins, mixin.Mixin)
        self.mixins = mixins

        self._attributes = {
            "occi.core.id": attribute.InmutableAttribute("occi.core.id", id),
            "occi.core.title": attribute.MutableAttribute("occi.core.title", title)
        }

        self._kind = kind.Kind(helpers.build_schema('core'), 'entity', 'entity',
                               self._attributes.values(), '/entity/')

    @property
    def kind(self):
        return self._kind

    @property
    def attributes(self):
        return self._attributes

    @property
    def id(self):
        return self._attributes["occi.core.id"].value

    @property
    def title(self):
        return self._attributes["occi.core.title"].value

    @title.setter
    def title(self, value):
        self._attributes["occi.core.title"].value = value
