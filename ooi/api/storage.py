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
from ooi.occi.core import collection
from ooi.occi.infrastructure import storage
from ooi.openstack import helpers


class Controller(base.Controller):
    def index(self, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req = self._get_req(req, path="/%s/os-volumes" % tenant_id)
        response = req.get_response(self.app)
        volumes = self.get_from_response(response, "volumes", [])
        occi_storage_resources = []
        if volumes:
            for v in volumes:
                s = storage.StorageResource(title=v["displayName"], id=v["id"])
                occi_storage_resources.append(s)

        return collection.Collection(resources=occi_storage_resources)

    def show(self, id, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id

        # get info from server
        req = self._get_req(req, path="/%s/os-volumes/%s" % (tenant_id, id))
        response = req.get_response(self.app)
        v = self.get_from_response(response, "volume", {})

        state = helpers.vol_state(v["status"])
        st = storage.StorageResource(title=v["displayName"], id=v["id"],
                                     size=v["size"], state=state)
        return [st]
