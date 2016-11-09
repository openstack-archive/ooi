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
from ooi.occi.core import mixin
from ooi.occi.core import resource
from ooi.occi import helpers

up = action.Action(helpers.build_scheme('infrastructure/network/action'),
                   "up", "up network instance")

down = action.Action(helpers.build_scheme('infrastructure/network/action'),
                     "down", "down network instance")


class NetworkResource(resource.Resource):
    attributes = attr.AttributeCollection({
        "occi.network.vlan": attr.MutableAttribute(
            "occi.network.vlan", description="802.1q VLAN identifier",
            attr_type=attr.AttributeType.string_type),
        "occi.network.label": attr.MutableAttribute(
            "occi.network.label", description="Tag based VLANs",
            attr_type=attr.AttributeType.string_type),
        "occi.network.state": attr.InmutableAttribute(
            "occi.network.state", description="Current state of the instance",
            attr_type=attr.AttributeType.string_type),
        "occi.network.state.message": attr.InmutableAttribute(
            "occi.network.state.message",
            description=("Human-readable explanation of the current instance "
                         "state"),
            attr_type=attr.AttributeType.string_type),
    })

    actions = (up, down)
    kind = kind.Kind(helpers.build_scheme('infrastructure'), 'network',
                     'network resource', attributes, 'network/',
                     actions=actions,
                     parent=resource.Resource.kind)

    def __init__(self, title, summary=None, id=None, vlan=None, label=None,
                 state=None, message=None, mixins=[]):
        super(NetworkResource, self).__init__(title, mixins, summary=summary,
                                              id=id)
        self.vlan = vlan
        self.label = label
        self.attributes["occi.network.state"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.network.state"], state))
        self.attributes["occi.network.state.message"] = (
            attr.InmutableAttribute(
                self.attributes["occi.network.state.message"], message))

    @property
    def vlan(self):
        return self.attributes["occi.network.vlan"].value

    @vlan.setter
    def vlan(self, value):
        self.attributes["occi.network.vlan"].value = value

    @property
    def label(self):
        return self.attributes["occi.network.label"].value

    @label.setter
    def label(self, value):
        self.attributes["occi.network.label"].value = value

    @property
    def state(self):
        return self.attributes["occi.network.state"].value

    @property
    def message(self):
        return self.attributes["occi.network.state.message"].value


ip_network = mixin.Mixin(
    helpers.build_scheme("infrastructure/network"),
    "ipnetwork", "IP Networking Mixin",
    attributes=attr.AttributeCollection({
        "occi.network.address": attr.MutableAttribute(
            "occi.network.address",
            description="Internet Protocol (IP) network address",
            attr_type=attr.AttributeType.string_type),
        "occi.network.gateway": attr.MutableAttribute(
            "occi.network.gateway",
            description="Internet Protocol (IP) network address",
            attr_type=attr.AttributeType.string_type),
        "occi.network.allocation": attr.MutableAttribute(
            "occi.network.allocation",
            description="Address allocation mechanism: dynamic, static",
            attr_type=attr.AttributeType.string_type),
    }),
    applies=[NetworkResource.kind])
