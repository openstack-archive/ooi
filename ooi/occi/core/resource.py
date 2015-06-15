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
from ooi.occi.core import link
from ooi.occi import helpers


class Resource(entity.Entity):
    """OCCI Resource.

    The heart of the OCCI Core Model is the Resource type. Any resource exposed
    through OCCI is a Resource or a sub-type thereof. A resource can be e.g. a
    virtual machine, a job in a job submission system, a user, etc.

    The Resource type is complemented by the Link type which associates one
    Resource instance with another. The Link type contains a number of common
    attributes that Link sub-types inherit.
    """

    attributes = attribute.AttributeCollection(["occi.core.summary"])

    kind = kind.Kind(helpers.build_scheme('core'), 'resource',
                     'resource', attributes, 'resource/',
                     related=[entity.Entity.kind])

    def __init__(self, title, mixins, id=None, summary=None):
        super(Resource, self).__init__(title, mixins, id=id)
        self.attributes["occi.core.summary"] = attribute.MutableAttribute(
            "occi.core.summary", summary)
        self._links = []

    def __eq__(self, other):
        return all([self.attributes[i].value == other.attributes[i].value
                    for i in self.attributes])

    @property
    def links(self):
        return self._links

    def link(self, target, mixins=[]):
        l = link.Link("", mixins, self, target)
        self._links.append(l)

    def add_link(self, link):
        self._links.append(link)

    @property
    def summary(self):
        return self.attributes["occi.core.summary"].value

    @summary.setter
    def summary(self, value):
        self.attributes["occi.core.summary"].value = value
