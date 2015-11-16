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
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link
from ooi.occi import validator as occi_validator


class Controller(base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.os_helper = ooi.api.helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def index(self, req):
        volumes = self.os_helper.get_volumes(req)
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

    def _get_attachment_from_id(self, req, attachment_id):
        try:
            server_id, vol_id = attachment_id.split('_', 1)
        except ValueError:
            raise exception.LinkNotFound(link_id=attachment_id)

        vols = self.os_helper.get_server_volumes_link(req, server_id)
        for v in vols:
            if vol_id == v["volumeId"]:
                return v
        raise exception.LinkNotFound(link_id=attachment_id)

    def show(self, req, id):
        v = self._get_attachment_from_id(req, id)
        c = compute.ComputeResource(title="Compute", id=v["serverId"])
        s = storage.StorageResource(title="Storage", id=v["volumeId"])
        return [storage_link.StorageLink(c, s, deviceid=v["device"])]

    def create(self, req, body):
        parser = req.get_parser()(req.headers, req.body)
        scheme = {"category": storage_link.StorageLink.kind}
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        attrs = obj.get("attributes", {})
        _, vol_id = ooi.api.helpers.get_id_with_kind(
            req,
            attrs.get("occi.core.target"),
            storage.StorageResource.kind)
        _, server_id = ooi.api.helpers.get_id_with_kind(
            req,
            attrs.get("occi.core.source"),
            compute.ComputeResource.kind)
        device = attrs.get("occi.storagelink.deviceid", None)
        attachment = self.os_helper.create_server_volumes_link(req,
                                                               server_id,
                                                               vol_id,
                                                               dev=device)
        c = compute.ComputeResource(title="Compute", id=server_id)
        s = storage.StorageResource(title="Storage", id=vol_id)
        l = storage_link.StorageLink(c, s, deviceid=attachment["device"])
        return collection.Collection(resources=[l])

    def delete(self, req, id):
        v = self._get_attachment_from_id(req, id)
        self.os_helper.delete_server_volumes_link(req,
                                                  v["serverId"], v["volumeId"])
        return []
