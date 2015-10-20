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

from ooi.occi.core import attribute as attr
from ooi.occi.core import kind
from ooi.occi.core import link
from ooi.occi import helpers


class StorageLink(link.Link):
    attributes = attr.AttributeCollection(["occi.storagelink.deviceid",
                                           "occi.storagelink.mountpoint",
                                           "occi.storagelink.state"])
    kind = kind.Kind(helpers.build_scheme('infrastructure'), 'storagelink',
                     'storage link resource', attributes, 'storagelink/',
                     related=[link.Link.kind])

    def __init__(self, source, target, deviceid=None, mountpoint=None,
                 state=None):

        # TODO(enolfc): is this a valid link id?
        link_id = '_'.join([source.id, target.id])
        super(StorageLink, self).__init__(None, [], source, target, link_id)

        self.attributes["occi.storagelink.deviceid"] = attr.MutableAttribute(
            "occi.storagelink.deviceid", deviceid)
        self.attributes["occi.storagelink.mountpoint"] = attr.MutableAttribute(
            "occi.storagelink.mountpoint", mountpoint)
        self.attributes["occi.storagelink.state"] = attr.InmutableAttribute(
            "occi.storagelink.state", state)

    @property
    def deviceid(self):
        return self.attributes["occi.storagelink.deviceid"].value

    @deviceid.setter
    def deviceid(self, value):
        self.attributes["occi.storagelink.deviceid"].value = value

    @property
    def mountpoint(self):
        return self.attributes["occi.storagelink.mountpoint"].value

    @mountpoint.setter
    def mountpoint(self, value):
        self.attributes["occi.storagelink.mountpoint"].value = value

    @property
    def state(self):
        return self.attributes["occi.storagelink.state"].value
