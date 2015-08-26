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
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import network

FLOATING_PREFIX = "floating"
FIXED_PREFIX = "fixed"


def _build_network(name, prefix=None):
    if prefix:
        network_id = '/'.join([prefix, name])
    else:
        network_id = name
    return network.NetworkResource(title=name,
                                   id=network_id,
                                   state="active",
                                   mixins=[network.ip_network])


class Controller(base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.os_helper = ooi.api.helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def _floating_index(self, req):
        pools = self.os_helper.get_floating_ip_pools(req)
        occi_network_resources = []
        if pools:
            occi_network_resources.append(_build_network(FLOATING_PREFIX))
        return occi_network_resources

    def index(self, req):
        occi_network_resources = self._floating_index(req)
        occi_network_resources.append(_build_network(FIXED_PREFIX))
        return collection.Collection(resources=occi_network_resources)

    def show(self, req, id):
        if id == FIXED_PREFIX:
            return [_build_network(id)]
        elif id == FLOATING_PREFIX:
            pools = self.os_helper.get_floating_ip_pools(req)
            if pools:
                return [_build_network(id)]
        raise exception.NetworkNotFound(resource_id=id)
