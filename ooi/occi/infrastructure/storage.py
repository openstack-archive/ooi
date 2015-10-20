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

from ooi.occi.core import action
from ooi.occi.core import attribute as attr
from ooi.occi.core import kind
from ooi.occi.core import resource
from ooi.occi import helpers

online = action.Action(helpers.build_scheme('infrastructure/storage/action'),
                       "online", "online storage instance")

offline = action.Action(helpers.build_scheme('infrastructure/storage/action'),
                        "offline", "offline storage instance")

backup = action.Action(helpers.build_scheme('infrastructure/storage/action'),
                       "backup", "backup storage instance")

snapshot = action.Action(helpers.build_scheme('infrastructure/storage/action'),
                         "snapshot", "snapshot storage instance")

resize = action.Action(helpers.build_scheme('infrastructure/storage/action'),
                       "resize", "resize storage instance")


class StorageResource(resource.Resource):
    attributes = attr.AttributeCollection(["occi.storage.size",
                                           "occi.storage.state"])
    actions = (online, offline, backup, snapshot, resize)
    kind = kind.Kind(helpers.build_scheme('infrastructure'), 'storage',
                     'storage resource', attributes, 'storage/',
                     actions=actions,
                     related=[resource.Resource.kind])

    def __init__(self, title, summary=None, id=None, size=None, state=None):
        mixins = []
        super(StorageResource, self).__init__(title, mixins, summary=summary,
                                              id=id)
        self.attributes["occi.storage.size"] = attr.MutableAttribute(
            "occi.storage.size", size)
        self.attributes["occi.storage.state"] = attr.InmutableAttribute(
            "occi.storage.state", state)

    @property
    def size(self):
        return self.attributes["occi.storage.size"].value

    @size.setter
    def size(self, value):
        self.attributes["occi.storage.size"].value = value

    @property
    def state(self):
        return self.attributes["occi.storage.state"].value
