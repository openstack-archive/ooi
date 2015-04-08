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

import uuid

import six

from ooi.occi.core import attribute
from ooi.occi.core import kind
from ooi.occi.core import mixin
from ooi.occi import helpers
from ooi import utils


class EntityMeta(type):
    """Meta class for Entity classes.

    Following OCCI Core model, all the Entity subclasses will have its own
    attributes, as long as they parent's ones.

    For example the Entity class defines "occi.core.id" and "occi.core.title"
    attributes, and the resource Resource class (that is a subclass of Entity)
    defines "occi.core.summary" as attributes. Therefore, the Resource class
    and all the objects should have all three attributes.

    This metaclass does this, by updating the attributes to those of the base
    class.
    """
    def __new__(cls, name, bases, dct):
        for kls in bases:
            if "attributes" in vars(kls):
                dct["attributes"].update(kls.attributes)

        return super(EntityMeta, cls).__new__(cls, name, bases, dct)

    def __init__(self, *args):
        super(EntityMeta, self).__init__(*args)


@six.add_metaclass(EntityMeta)
class Entity(object):
    """OCCI Entity.

    Entity is an abstract type, which both Resource and Link inherit. Each
    sub-type of Entity is identified by a unique Kind instance
    """

    attributes = attribute.AttributeCollection(["occi.core.id",
                                                "occi.core.title"])

    kind = kind.Kind(helpers.build_scheme('core'), 'entity',
                     'entity', attributes, 'entity/')

    def __init__(self, title, mixins, id=None):
        helpers.check_type(mixins, mixin.Mixin)
        self.mixins = mixins

        # NOTE(aloga): we need a copy of the attributes, otherwise we will be
        # using the class ones instead of the object ones.
        self.attributes = self.attributes.copy()

        # damn, we're shading a builtin
        if id is None:
            id = uuid.uuid4().hex

        self.attributes["occi.core.id"] = attribute.InmutableAttribute(
            "occi.core.id", id)
        self.attributes["occi.core.title"] = attribute.MutableAttribute(
            "occi.core.title", title)

    @property
    def id(self):
        return self.attributes["occi.core.id"].value

    @property
    def title(self):
        return self.attributes["occi.core.title"].value

    @title.setter
    def title(self, value):
        self.attributes["occi.core.title"].value = value

    @property
    def location(self):
        return utils.join_url(self.kind.location, self.id)
