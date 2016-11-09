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
from ooi.occi.core import mixin
from ooi.occi import helpers


class NetworkInterface(link.Link):
    attributes = attr.AttributeCollection({
        "occi.networkinterface.interface": attr.InmutableAttribute(
            "occi.networkinterface.interface",
            description=("Identifier that relates the link to the link's "
                         "device interface."),
            attr_type=attr.AttributeType.string_type),
        "occi.networkinterface.mac": attr.MutableAttribute(
            "occi.networkinterface.mac",
            description=("MAC address associated with the link's device "
                         "interface."),
            attr_type=attr.AttributeType.string_type),
        "occi.networkinterface.state": attr.InmutableAttribute(
            "occi.networkinterface.state",
            description="Current state of the instance",
            attr_type=attr.AttributeType.string_type),
        "occi.networkinterface.state.message": attr.InmutableAttribute(
            "occi.networkinterface.state.message",
            description=("Human-readable explanation of the current instance "
                         "state"),
            attr_type=attr.AttributeType.string_type),
    })

    kind = kind.Kind(helpers.build_scheme('infrastructure'),
                     'networkinterface', 'network link resource',
                     attributes, 'networklink/',
                     parent=link.Link.kind)

    def __init__(self, mixins, source, target, id=None, interface=None,
                 mac=None, state=None, message=None):

        super(NetworkInterface, self).__init__(None, mixins, source,
                                               target, id)

        self.attributes["occi.networkinterface.interface"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.networkinterface.interface"], interface))
        self.mac = mac
        self.attributes["occi.networkinterface.state"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.networkinterface.state"], state))
        self.attributes["occi.networkinterface.state.message"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.networkinterface.state.message"],
                message))

    @property
    def interface(self):
        return self.attributes["occi.networkinterface.interface"].value

    @property
    def mac(self):
        return self.attributes["occi.networkinterface.mac"].value

    @mac.setter
    def mac(self, value):
        self.attributes["occi.networkinterface.mac"].value = value

    @property
    def state(self):
        return self.attributes["occi.networkinterface.state"].value

    @property
    def message(self):
        return self.attributes["occi.networkinterface.state.message"].value

ip_network_interface = mixin.Mixin(
    helpers.build_scheme("infrastructure/networkinterface"),
    "ipnetworkinterface", "IP Network interface Mixin",
    attributes=attr.AttributeCollection({
        "occi.networkinterface.address": attr.MutableAttribute(
            "occi.networkinterface.address",
            description="Internet Protocol (IP) network address of the link",
            attr_type=attr.AttributeType.string_type),
        "occi.networkinterface.gateway": attr.MutableAttribute(
            "occi.networkinterface.gateway",
            description="Internet Protocol (IP) network address",
            attr_type=attr.AttributeType.string_type),
        "occi.networkinterface.allocation": attr.MutableAttribute(
            "occi.networkinterface.allocation",
            description="Address allocation mechanism: dynamic, static",
            attr_type=attr.AttributeType.string_type),
    }),
    applies=[NetworkInterface.kind])
