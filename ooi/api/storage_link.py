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

import json

import webob.exc

from ooi.api import base
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link


class Controller(base.Controller):
    def index(self, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req = self._get_req(req, path="/%s/os-volumes" % tenant_id)
        response = req.get_response(self.app)
        volumes = self.get_from_response(response, "volumes", [])
        occi_link_resources = []
        for v in volumes:
            for attach in v["attachments"]:
                if attach:
                    c = compute.ComputeResource(title="Compute",
                                                id=attach["serverId"])
                    s = storage.StorageResource(title="Storage", id=v["id"])
                    l = storage_link.StorageLink(c, s,
                                                 deviceid=attach["device"])
                    occi_link_resources.append(l)

        return collection.Collection(resources=occi_link_resources)

    def _get_attachment_from_id(self, req, id):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        server_id, vol_id = id.split('_', 1)

        req_path = "/%s/servers/%s/os-volume_attachments" % (tenant_id,
                                                             server_id)
        req = self._get_req(req, path=req_path, method="GET")
        response = req.get_response(self.app)
        vols = self.get_from_response(response, "volumeAttachments", [])
        for v in vols:
            if vol_id == v["volumeId"]:
                return v
        raise webob.exc.HTTPNotFound()

    def show(self, req, id):
        v = self._get_attachment_from_id(req, id)
        c = compute.ComputeResource(title="Compute", id=v["serverId"])
        s = storage.StorageResource(title="Storage", id=v["volumeId"])
        return [storage_link.StorageLink(c, s, deviceid=v["device"])]

    @base.Controller.validate({"kind": storage_link.StorageLink.kind})
    def create(self, obj, req, body):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        vol_id = obj["attributes"]["occi.core.target"]
        server_id = obj["attributes"]["occi.core.source"]
        req_body = {
            "volumeAttachment": {
                "volumeId": vol_id
            }
        }
        try:
            device = obj["attributes"]["occi.storagelink.deviceid"]
            req_body["volumeAttachment"]["device"] = device
        except KeyError:
            pass
        req_path = "/%s/servers/%s/os-volume_attachments" % (tenant_id,
                                                             server_id)
        req = self._get_req(req,
                            path=req_path,
                            content_type="application/json",
                            body=json.dumps(req_body))
        response = req.get_response(self.app)
        attachment = self.get_from_response(response, "volumeAttachment", {})
        c = compute.ComputeResource(title="Compute", id=server_id)
        s = storage.StorageResource(title="Storage", id=vol_id)
        return [storage_link.StorageLink(c, s, deviceid=attachment["device"])]

    def delete(self, req, id):
        v = self._get_attachment_from_id(req, id)
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req_path = ("/%s/servers/%s/os-volume_attachments/%s"
                    % (tenant_id, v["serverId"], v["id"]))
        req = self._get_req(req, path=req_path, method="DELETE")
        response = req.get_response(self.app)
        if response.status_int not in [202]:
            raise base.exception_from_response(response)
