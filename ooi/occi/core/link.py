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
from ooi.occi.core import entity
from ooi.occi.core import kind
from ooi.occi import helpers


class Link(entity.Entity):
    """OCCI Resoure.

    The Resource type is complemented by the Link type which associates one
    Resource instance with another.
    """

    attributes = attribute.AttributeCollection(["occi.core.source",
                                                "occi.core.target"])

    kind = kind.Kind(helpers.build_scheme("core"), 'link', 'link',
                     attributes, 'link/')

    def __init__(self, title, mixins, source, target, id=None):
        super(Link, self).__init__(title, mixins, id)
        self.attributes["occi.core.source"] = attribute.MutableAttribute(
            "occi.core.source", source)
        self.attributes["occi.core.target"] = attribute.MutableAttribute(
            "occi.core.target", target)

    @property
    def source(self):
        return self.attributes["occi.core.source"].value

    @source.setter
    def source(self, value):
        self.attributes["occi.core.source"].value = value

    @property
    def target(self):
        return self.attributes["occi.core.target"].value

    @target.setter
    def target(self, value):
        self.attributes["occi.core.target"].value = value
