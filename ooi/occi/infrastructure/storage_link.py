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
    attributes = attr.AttributeCollection({
        "occi.storagelink.deviceid": attr.MutableAttribute(
            "occi.storagelink.deviceid",
            description=("Device identifier as defined by the OCCI service "
                         "provider"),
            attr_type=attr.AttributeType.string_type),
        "occi.storagelink.mountpoint": attr.MutableAttribute(
            "occi.storagelink.mountpoint",
            description=("Point to where the storage is mounted "
                         "in the guest OS"),
            attr_type=attr.AttributeType.string_type),
        "occi.storagelink.state": attr.InmutableAttribute(
            "occi.storagelink.state",
            description="Current state of the instance",
            attr_type=attr.AttributeType.string_type),
        "occi.storagelink.state.message": attr.InmutableAttribute(
            "occi.storagelink.state.message",
            description=("Human-readable explanation of the current instance "
                         "state"),
            attr_type=attr.AttributeType.string_type),
    })
    kind = kind.Kind(helpers.build_scheme('infrastructure'), 'storagelink',
                     'storage link resource', attributes, 'storagelink/',
                     parent=link.Link.kind)

    def __init__(self, source, target, deviceid=None, mountpoint=None,
                 state=None, message=None):

        # TODO(enolfc): is this a valid link id?
        link_id = '_'.join([source.id, target.id])
        super(StorageLink, self).__init__(None, [], source, target, link_id)

        self.deviceid = deviceid
        self.mountpoint = mountpoint
        self.attributes["occi.storagelink.state"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.storagelink.state"], state))
        self.attributes["occi.storagelink.state.message"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.storagelink.state.message"], message))

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

    @property
    def message(self):
        return self.attributes["occi.storagelink.state.message"].value
