# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
# Copyright 2016 LIP - Lisbon
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
from ooi.occi.core import mixin
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.openstack import helpers


class OSFloatingIPPool(mixin.Mixin):
    scheme = helpers.build_scheme("network/floatingippool")

    def __init__(self, pool=None):
        super(OSFloatingIPPool, self).__init__(self.scheme, pool, pool)


class OSNetworkInterface(network_link.NetworkInterface):
    attributes = attr.AttributeCollection(["occi.networkinterface.address",
                                           "occi.networkinterface.gateway",
                                           "occi.networkinterface.allocation"])

    def __init__(self, source, target, mac, address, ip_id=None,
                 pool=None, state='active'):
        link_id = '_'.join([source.id, target.id, address])
        mixins = [network_link.ip_network_interface]
        if pool:
            mixins.append(OSFloatingIPPool(pool))
        super(OSNetworkInterface, self).__init__(mixins, source, target,
                                                 link_id, "eth0", mac,
                                                 state)
        self.ip_id = ip_id
        self.attributes["occi.networkinterface.address"] = (
            attr.MutableAttribute("occi.networkinterface.address", address))
        self.attributes["occi.networkinterface.gateway"] = (
            attr.MutableAttribute("occi.networkinterface.gateway", None))
        self.attributes["occi.networkinterface.allocation"] = (
            attr.MutableAttribute("occi.networkinterface.allocation",
                                  "dynamic"))

    @property
    def address(self):
        return self.attributes["occi.networkinterface.address"].value

    @address.setter
    def address(self, value):
        self.attributes["occi.networkinterface.address"].value = value

    @property
    def gateway(self):
        return self.attributes["occi.networkinterface.gateway"].value

    @gateway.setter
    def gateway(self, value):
        self.attributes["occi.networkinterface.gateway"].value = value

    @property
    def allocation(self):
        return self.attributes["occi.networkinterface.allocation"].value

    @allocation.setter
    def allocation(self, value):
        self.attributes["occi.networkinterface.allocation"].value = value


class OSNetwork(mixin.Mixin):
    scheme = helpers.build_scheme("infrastructure/network")

    def __init__(self, pool=None):
        term = "osnetwork"
        title = "openstack network"

        super(OSNetwork, self).__init__(
            scheme=self.scheme,
            term=term,
            title=title,
            attributes=attr.AttributeCollection([
                "org.openstack.network.ip_version"
            ])
        )


os_network = OSNetwork()


class OSNetworkResource(network.NetworkResource):

    attributes = attr.AttributeCollection([
        "org.openstack.network.ip_version",
        "occi.network.address",
        "occi.network.gateway",
        "occi.network.allocation",
    ])

    def __init__(self, title=None, summary=None,
                 id=None, vlan=None, label=None, state=None,
                 address=None, gateway=None, ip_version=None, allocation=None):

        super(OSNetworkResource,
              self).__init__(title=title,
                             summary=summary, id=id, vlan=vlan,
                             label=label, state=state,
                             mixins=[network.ip_network, OSNetwork()])
        # subnet
        self.attributes["org.openstack.network.ip_version"] = (
            attr.MutableAttribute(
                "org.openstack.network.ip_version", ip_version))
        self.attributes["occi.network.address"] = (
            attr.MutableAttribute(
                "occi.network.address", address))
        self.attributes["occi.network.gateway"] = (
            attr.MutableAttribute(
                "occi.network.gateway", gateway))
        self.attributes["occi.network.allocation"] = (
            attr.MutableAttribute(
                "occi.network.allocation", allocation))

    @property
    def ip_version(self):
        return self.attributes["org.openstack.network.ip_version"].value

    @ip_version.setter
    def ip_version(self, value):
        self.attributes["org.openstack.network.ip_version"].value = value

    @property
    def address(self):
        return self.attributes["occi.network.address"].value

    @address.setter
    def address(self, value):
        self.attributes["occi.network.address"].value = value

    @property
    def gateway(self):
        return self.attributes["occi.network.gateway"].value

    @gateway.setter
    def gateway(self, value):
        self.attributes["occi.network.gateway"].value = value

    @property
    def allocation(self):
        return self.attributes["occi.network.network.allocation"].value

    @allocation.setter
    def allocation(self, value):
        self.attributes["occi.network.network.allocation"] = value
