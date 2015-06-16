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

import ooi.api.base
import ooi.api.network as network_api
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link
from ooi.occi import validator as occi_validator
from ooi.openstack import contextualization
from ooi.openstack import helpers
from ooi.openstack import network as os_network
from ooi.openstack import templates


def _create_network_link(addr, comp, floating_ips):
    if addr["OS-EXT-IPS:type"] == "floating":
        for ip in floating_ips:
            if addr["addr"] == ip["ip"]:
                net = network.NetworkResource(
                    title="network",
                    id="%s/%s" % (network_api.FLOATING_PREFIX, ip["pool"]))
    else:
        net = network.NetworkResource(title="network", id="fixed")
    return os_network.OSNetworkInterface(comp, net,
                                         addr["OS-EXT-IPS-MAC:mac_addr"],
                                         addr["addr"])


class Controller(ooi.api.base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.compute_actions = compute.ComputeResource.actions

    def _get_compute_resources(self, servers):
        occi_compute_resources = []
        if servers:
            for s in servers:
                s = compute.ComputeResource(title=s["name"], id=s["id"])
                occi_compute_resources.append(s)

        return occi_compute_resources

    def _get_compute_ids(self, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req = self._get_req(req,
                            path="/%s/servers" % tenant_id,
                            method="GET")
        response = req.get_response(self.app)
        return [s["id"] for s in self.get_from_response(response,
                                                        "servers", [])]

    def _get_os_delete_req(self, req, server_id):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        path = "/%s/servers/%s" % (tenant_id, server_id)
        req = self._get_req(req, path=path, method="DELETE")
        return req

    def _delete(self, req, server_ids):
        for server_id in server_ids:
            os_req = self._get_os_delete_req(req, server_id)
            response = os_req.get_response(self.app)
            if response.status_int not in [204]:
                raise ooi.api.base.exception_from_response(response)
        return []

    def _get_os_index_req(self, req):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        req = self._get_req(req, path="/%s/servers" % tenant_id)
        return req

    def index(self, req):
        os_req = self._get_os_index_req(req)
        response = os_req.get_response(self.app)
        servers = self.get_from_response(response, "servers", [])
        occi_compute_resources = self._get_compute_resources(servers)

        return collection.Collection(resources=occi_compute_resources)

    def _get_os_run_action(self, req, action, server_id):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        path = "/%s/servers/%s/action" % (tenant_id, server_id)

        actions_map = {
            "stop": {"os-stop": None},
            "start": {"os-start": None},
            "restart": {"reboot": {"type": "SOFT"}},
        }
        action = actions_map[action]

        body = json.dumps(action)
        req = self._get_req(req, path=path, body=body, method="POST")
        return req

    def run_action(self, req, id, body):
        action = req.GET.get("action", None)
        occi_actions = [a.term for a in compute.ComputeResource.actions]

        if action is None or action not in occi_actions:
            raise exception.InvalidAction(action=action)

        parser = req.get_parser()(req.headers, req.body)
        obj = parser.parse()

        if action == "stop":
            scheme = {"category": compute.stop}
        elif action == "start":
            scheme = {"category": compute.start}
        elif action == "restart":
            scheme = {"category": compute.restart}
        else:
            raise exception.NotImplemented

        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        os_req = self._get_os_run_action(req, action, id)
        response = os_req.get_response(self.app)
        if response.status_int != 202:
            raise ooi.api.base.exception_from_response(response)
        return []

    def create(self, req, body):
        tenant_id = req.environ["keystone.token_auth"].user.project_id
        parser = req.get_parser()(req.headers, req.body)
        scheme = {
            "category": compute.ComputeResource.kind,
            "mixins": [
                templates.OpenStackOSTemplate,
                templates.OpenStackResourceTemplate,
            ],
            "optional_mixins": [
                contextualization.user_data,
                contextualization.public_key,
            ]
        }
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        attrs = obj.get("attributes", {})
        name = attrs.get("occi.core.title", "OCCI VM")
        image = obj["schemes"][templates.OpenStackOSTemplate.scheme][0]
        flavor = obj["schemes"][templates.OpenStackResourceTemplate.scheme][0]
        req_body = {"server": {
            "name": name,
            "imageRef": image,
            "flavorRef": flavor,
        }}
        if contextualization.user_data.scheme in obj["schemes"]:
            req_body["user_data"] = attrs.get(
                "org.openstack.compute.user_data")
        # TODO(enolfc): add here the correct metadata info
        # if contextualization.public_key.scheme in obj["schemes"]:
        #     req_body["metadata"] = XXX
        req = self._get_req(req,
                            path="/%s/servers" % tenant_id,
                            content_type="application/json",
                            body=json.dumps(req_body))
        response = req.get_response(self.app)
        # We only get one server
        server = self.get_from_response(response, "server", {})

        # The returned JSON does not contain the server name
        server["name"] = name
        occi_compute_resources = self._get_compute_resources([server])

        return collection.Collection(resources=occi_compute_resources)

    def show(self, req, id):
        tenant_id = req.environ["keystone.token_auth"].user.project_id

        # get info from server
        req = self._get_req(req, path="/%s/servers/%s" % (tenant_id, id))
        response = req.get_response(self.app)
        s = self.get_from_response(response, "server", {})

        # get info from flavor
        req = self._get_req(req, path="/%s/flavors/%s" % (tenant_id,
                                                          s["flavor"]["id"]))
        response = req.get_response(self.app)
        flavor = self.get_from_response(response, "flavor", {})
        res_tpl = templates.OpenStackResourceTemplate(flavor["id"],
                                                      flavor["name"],
                                                      flavor["vcpus"],
                                                      flavor["ram"],
                                                      flavor["disk"])

        # get info from image
        req = self._get_req(req, path="/%s/images/%s" % (tenant_id,
                                                         s["image"]["id"]))
        response = req.get_response(self.app)
        image = self.get_from_response(response, "image", {})
        os_tpl = templates.OpenStackOSTemplate(image["id"],
                                               image["name"])

        # build the compute object
        comp = compute.ComputeResource(title=s["name"], id=s["id"],
                                       cores=flavor["vcpus"],
                                       hostname=s["name"],
                                       memory=flavor["ram"],
                                       state=helpers.vm_state(s["status"]),
                                       mixins=[os_tpl, res_tpl])

        # storage links
        req = self._get_req(req, path=("/%s/servers/%s/os-volume_attachments"
                                       % (tenant_id, s["id"])))
        response = req.get_response(self.app)
        vols = self.get_from_response(response, "volumeAttachments", [])
        for v in vols:
            st = storage.StorageResource(title="storage", id=v["volumeId"])
            comp.add_link(storage_link.StorageLink(comp, st,
                                                   deviceid=v["device"]))

        # network links
        addresses = s.get("addresses", {})
        if addresses:
            req = self._get_req(req, path="/%s/os-floating-ips" % tenant_id)
            response = req.get_response(self.app)
            floating_ips = self.get_from_response(response, "floating_ips", [])
            for addr_set in addresses.values():
                for addr in addr_set:
                    comp.add_link(_create_network_link(addr, comp,
                                                       floating_ips))

        return [comp]

    def delete(self, req, id):
        return self._delete(req, [id])

    def delete_all(self, req):
        return self._delete(req, self._get_compute_ids(req))
