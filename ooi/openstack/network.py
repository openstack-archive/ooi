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
from ooi.occi.infrastructure import network_link


class OSNetworkInterface(network_link.NetworkInterface):
    attributes = attr.AttributeCollection(["occi.networkinterface.address",
                                           "occi.networkinterface.gateway",
                                           "occi.networkinterface.allocation"])

    def __init__(self, source, target, mac, address):
        link_id = '_'.join([source.id, address])
        mixins = [network_link.ip_network_interface]
        super(OSNetworkInterface, self).__init__(mixins, source, target,
                                                 link_id, "eth0", mac,
                                                 "active")
        self.attributes["occi.networkinterface.address"] = (
            attr.MutableAttribute("occi.networkinterface.address", address))
        self.attributes["occi.networkinterface.gateway"] = (
            attr.MutableAttribute("occi.networkinterface.gateway", None))
        self.attributes["occi.networkinterface.allocation"] = (
            attr.MutableAttribute("occi.networkinterface.allocation",
                                  "dynamic"))
