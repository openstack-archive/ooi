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


from ooi.occi import helpers
from ooi.occi.core import attribute
from ooi.occi.core import entity
from ooi.occi.core import kind


class Link(entity.Entity):
    """OCCI Resoure.

    The Resource type is complemented by the Link type which associates one
    Resource instance with another.
    """


    def __init__(self, id, title, mixins, source, target):
        super(Link, self).__init__(id, title, mixins)

        cls_attrs = {
            "occi.core.source": attribute.MutableAttribute("occi.core.source", source),
            "occi.core.target": attribute.MutableAttribute("occi.core.target", target),
        }
        self._attributes.update(cls_attrs)
        self._kind = kind.Kind(helpers.build_schema("core"), 'link', 'link', self._attributes.values(), '/link/')

    @property
    def source(self):
        return self._attributes["occi.core.source"].value

    @source.setter
    def source(self, value):
        self._attributes["occi.core.source"].value = value

    @property
    def target(self):
        return self._attributes["occi.core.target"].value

    @target.setter
    def target(self, value):
        self._attributes["occi.core.target"].value = value
