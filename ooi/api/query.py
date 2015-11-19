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

from ooi.api import base
import ooi.api.helpers
from ooi.occi.core import entity
from ooi.occi.core import link
from ooi.occi.core import resource
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import network_link
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link
from ooi.occi.infrastructure import templates as infra_templates
from ooi.openstack import contextualization
from ooi.openstack import network as os_network
from ooi.openstack import templates


class Controller(base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.os_helper = ooi.api.helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def _resource_tpls(self, req):
        flavors = self.os_helper.get_flavors(req)
        occi_resource_templates = []
        if flavors:
            for f in flavors:
                tpl = templates.OpenStackResourceTemplate(f["id"],
                                                          f["name"],
                                                          f["vcpus"],
                                                          f["ram"],
                                                          f["disk"])
                occi_resource_templates.append(tpl)
        return occi_resource_templates

    def _os_tpls(self, req):
        images = self.os_helper.get_images(req)
        occi_os_templates = []
        if images:
            for i in images:
                tpl = templates.OpenStackOSTemplate(i["id"], i["name"])
                occi_os_templates.append(tpl)
        return occi_os_templates

    def _ip_pools(self, req):
        pools = self.os_helper.get_floating_ip_pools(req)
        occi_ip_pools = []
        if pools:
            for p in pools:
                occi_ip_pools.append(os_network.OSFloatingIPPool(p["name"]))
        return occi_ip_pools

    def index(self, req):
        l = []
        # OCCI Core Kinds:
        l.append(entity.Entity.kind)
        l.append(resource.Resource.kind)
        l.append(link.Link.kind)

        # OCCI infra Compute:
        l.append(compute.ComputeResource.kind)
        l.extend(compute.ComputeResource.actions)

        # OCCI infra Storage
        l.append(storage.StorageResource.kind)
        l.append(storage_link.StorageLink.kind)
        l.extend(storage.StorageResource.actions)

        # OCCI infra network
        l.append(network.NetworkResource.kind)
        l.extend(network.NetworkResource.actions)
        l.append(network.ip_network)
        l.append(network_link.NetworkInterface.kind)
        l.append(network_link.ip_network_interface)

        # OCCI infra compute mixins
        l.append(infra_templates.os_tpl)
        l.append(infra_templates.resource_tpl)

        # OpenStack flavors & images
        l.extend(self._resource_tpls(req))
        l.extend(self._os_tpls(req))

        # OpenStack Contextualization
        l.append(contextualization.user_data)
        l.append(contextualization.public_key)

        # OpenStack Floating IP Pools
        l.extend(self._ip_pools(req))
        return l
