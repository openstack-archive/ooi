# -*- coding: utf-8 -*-

# Copyright 2015 LIP - Lisbon
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
from ooi.occi.infrastructure.network import NetworkResource
from ooi.occi import helpers


class Network(NetworkResource):
    attributes = attr.AttributeCollection(["occi.network.shared",
                                           "occi.network.adminstate",
                                           "occi.network.tenantid",
                                           "occi.network.ip_version",
                                           "occi.networkinterface.address",
                                           "occi.networkinterface.gateway",
                                           ])
    scheme = helpers.build_scheme("infrastructure/network",)
    term = "networks"
    kind = kind.Kind(scheme, term, 'network extended', attributes=attributes,
                     location='networks/',  related=[NetworkResource.kind])

    def __init__(self, title=None, summary=None, id=None,vlan=None, label=None, state=None,
                 shared=None, adminstate=None, tenantid=None, address=None
                 , gateway=None, ip_version=None):
        super(Network, self).__init__(title=title, summary=summary, id=id, vlan=vlan,
                                      label=label, state=state)
        self.attributes["occi.network.shared"] = attr.MutableAttribute(
            "occi.network.shared", shared)
        self.attributes["occi.network.adminstate"] = attr.MutableAttribute(
            "occi.network.adminstate", adminstate)
        self.attributes["occi.network.tenantid"] = attr.MutableAttribute(
            "occi.network.tenantid", tenantid)
        #subnet
        self.attributes["occi.network.ip_version"] = attr.InmutableAttribute(
            "occi.network.ip_version", ip_version)
        self.attributes["occi.networkinterface.address"] = attr.InmutableAttribute(
            "occi.networkinterface.address", address)
        self.attributes["occi.networkinterface.gateway"] = attr.InmutableAttribute(
            "occi.networkinterface.gateway", gateway)

    @property
    def shared(self):
        return self.attributes["occi.network.shared"].value

    @shared.setter
    def shared(self, value):
        self.attributes["occi.network.shared"].value = value

    @property
    def adminstate(self):
        return self.attributes["occi.network.adminstate"].value

    @adminstate.setter
    def adminstate(self, value):
        self.attributes["occi.network.adminstate"].value = value

    @property
    def tenantid(self):
        return self.attributes["occi.network.tenantid"].value

    # SUBRED
    @property
    def ip_version(self):
        return self.attributes["occi.network.ip_version"].value

    @property
    def address(self):
        return self.attributes["occi.networkinterface.address"].value

    @property
    def gateway(self):
        return self.attributes["occi.networkinterface.gateway"].value