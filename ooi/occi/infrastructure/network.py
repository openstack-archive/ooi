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
from ooi.occi.core import mixin
from ooi.occi.core import resource
from ooi.occi import helpers

up = action.Action(helpers.build_scheme('infrastructure/network/action'),
                   "up", "up network instance")

down = action.Action(helpers.build_scheme('infrastructure/network/action'),
                     "down", "down network instance")


class NetworkResource(resource.Resource):
    attributes = attr.AttributeCollection(["occi.network.vlan",
                                           "occi.network.label",
                                           "occi.network.state"])
    actions = (up, down)
    kind = kind.Kind(helpers.build_scheme('infrastructure'), 'network',
                     'network resource', attributes, 'network/',
                     actions=actions,
                     related=[resource.Resource.kind])

    def __init__(self, title, summary=None, id=None, vlan=None, label=None,
                 state=None, mixins=[]):
        super(NetworkResource, self).__init__(title, mixins, summary=summary,
                                              id=id)
        self.attributes["occi.network.vlan"] = attr.MutableAttribute(
            "occi.network.vlan", vlan)
        self.attributes["occi.network.label"] = attr.MutableAttribute(
            "occi.network.label", label)
        self.attributes["occi.network.state"] = attr.InmutableAttribute(
            "occi.network.state", state)

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


ip_network = mixin.Mixin(helpers.build_scheme("infrastructure/network"),
                         "ipnetwork", "IP Networking Mixin",
                         attributes=attr.AttributeCollection([
                             "occi.network.address",
                             "occi.network.gateway",
                             "occi.network.allocation"]))
