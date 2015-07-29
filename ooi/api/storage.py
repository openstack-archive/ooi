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
from ooi.occi.infrastructure import storage
from ooi.occi import validator as occi_validator
from ooi.openstack import helpers


class Controller(base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.os_helper = ooi.api.helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def index(self, req):
        volumes = self.os_helper.get_volumes(req)
        occi_storage_resources = []
        if volumes:
            for v in volumes:
                s = storage.StorageResource(title=v["displayName"], id=v["id"])
                occi_storage_resources.append(s)

        return collection.Collection(resources=occi_storage_resources)

    def show(self, req, id):
        v = self.os_helper.get_volume(req, id)

        state = helpers.vol_state(v["status"])
        st = storage.StorageResource(title=v["displayName"], id=v["id"],
                                     size=v["size"], state=state)
        return [st]

    def create(self, req, body):
        parser = req.get_parser()(req.headers, req.body)
        scheme = {"category": storage.StorageResource.kind}
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        attrs = obj.get("attributes", {})
        name = attrs.get("occi.core.title", "OCCI Volume")
        # TODO(enolfc): this should be handled by the validator
        try:
            size = attrs["occi.storage.size"]
        except KeyError:
            raise exception.Invalid()

        volume = self.os_helper.volume_create(req, name, size)

        st = storage.StorageResource(title=volume["displayName"],
                                     id=volume["id"],
                                     size=volume["size"],
                                     state=helpers.vol_state(volume["status"]))
        return collection.Collection(resources=[st])

    def _delete(self, req, vol_ids):
        for vol_id in vol_ids:
            self.os_helper.volume_delete(req, vol_id)
        return []

    # TODO(enolfc): these two methods could be in the base.Controller
    # they are identical to the ones of the Compute
    def delete(self, req, id):
        return self._delete(req, [id])

    def delete_all(self, req):
        ids = [v["id"] for v in self.os_helper.get_volumes(req)]
        return self._delete(req, ids)

    # TODO(enolfc): implement the actions.
    def run_action(self, req, id, body):
        action = req.GET.get("action", None)
        actions = [a.term for a in storage.StorageResource.actions]

        if action is None or action not in actions:
            raise exception.InvalidAction(action=action)

        raise exception.NotImplemented()
