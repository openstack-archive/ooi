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

import uuid

import webob.exc

import ooi.api.base
import ooi.api.helpers
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import contextualization
from ooi.occi.infrastructure import ip_reservation
from ooi.occi.infrastructure import network
from ooi.occi.infrastructure import storage
from ooi.occi.infrastructure import storage_link
from ooi.occi import validator as occi_validator
from ooi.openstack import contextualization as os_contextualization
from ooi.openstack import helpers
from ooi.openstack import network as os_network
from ooi.openstack import templates


def _create_network_link(addr, comp, net_id, type_ip):
    if type_ip == "floating":
        net = ip_reservation.IPReservation(title="network",
                                           address=None,
                                           id=net_id)
    else:
        net = network.NetworkResource(title="network", id=net_id)
    return os_network.OSNetworkInterface(comp, net,
                                         addr["OS-EXT-IPS-MAC:mac_addr"],
                                         addr["addr"])


class Controller(ooi.api.base.Controller):
    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.compute_actions = compute.ComputeResource.actions
        self.os_helper = ooi.api.helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def _get_compute_resources(self, servers):
        occi_compute_resources = []
        if servers:
            for s in servers:
                s = compute.ComputeResource(title=s["name"], id=s["id"])
                occi_compute_resources.append(s)

        return occi_compute_resources

    def index(self, req):
        servers = self.os_helper.index(req)
        occi_compute_resources = self._get_compute_resources(servers)

        return collection.Collection(resources=occi_compute_resources)

    def run_action(self, req, id, body):
        action = req.GET.get("action", None)
        occi_actions = [a.term for a in compute.ComputeResource.actions]

        if action is None or action not in occi_actions:
            raise exception.InvalidAction(action=action)

        parser = req.get_parser()(req.headers, req.body)
        obj = parser.parse()

        server = self.os_helper.get_server(req, id)

        if action == "stop":
            scheme = {"category": compute.stop}
        elif action == "start":
            scheme = {"category": compute.start}
            if server["status"] == "SUSPENDED":
                action = "resume"
            elif server["status"] == "PAUSED":
                action = "unpause"
        elif action == "restart":
            scheme = {"category": compute.restart}
        elif action == "suspend":
            scheme = {"category": compute.suspend}
        else:
            raise exception.NotImplemented

        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        self.os_helper.run_action(req, action, id)
        return []

    def _build_block_mapping(self, req, obj):
        mappings = []
        links = obj.get("links", {})
        for l in links.get(storage.StorageResource.kind.type_id, []):
            _, vol_id = ooi.api.helpers.get_id_with_kind(
                req,
                l.get("target"),
                storage.StorageResource.kind)
            mapping = {
                "source_type": "volume",
                "uuid": vol_id,
                "delete_on_termination": False,
            }
            try:
                device_name = l['attributes']['occi.storagelink.deviceid']
                mapping['device_name'] = device_name
            except KeyError:
                pass
            mappings.append(mapping)
        # this needs to be there if we have a mapping
        if mappings:
            image = obj["schemes"][templates.OpenStackOSTemplate.scheme][0]
            mappings.insert(0, {
                "source_type": "image",
                "destination_type": "local",
                "boot_index": 0,
                "delete_on_termination": True,
                "uuid": image,
            })
        return mappings

    def _get_network_from_req(self, req, obj):
        networks = []
        links = obj.get("links", {})
        for l in links.get(network.NetworkResource.kind.type_id, []):
            _, net_id = ooi.api.helpers.get_id_with_kind(
                req,
                l.get("target"),
                network.NetworkResource.kind)
            net = {'uuid': net_id}
            networks.append(net)
        return networks

    def create(self, req, body):
        parser = req.get_parser()(req.headers, req.body)
        scheme = {
            "category": compute.ComputeResource.kind,
            "mixins": [
                templates.OpenStackOSTemplate,
                templates.OpenStackResourceTemplate,
            ],
            "optional_mixins": [
                contextualization.user_data,
                contextualization.ssh_key,
                os_contextualization.user_data,
                os_contextualization.public_key,
            ],
            "optional_links": [
                storage.StorageResource.kind,
                network.NetworkResource.kind,
            ]

        }
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)

        attrs = obj.get("attributes", {})
        name = attrs.get("occi.core.title", "OCCI_VM")
        image = obj["schemes"][templates.OpenStackOSTemplate.scheme][0]
        flavor = obj["schemes"][templates.OpenStackResourceTemplate.scheme][0]
        user_data, key_name, key_data = None, None, None
        create_key, create_key_tmp = False, False
        # TODO(enolfc): deprecate OS Contextualization in the future
        # meanwhile, raise 409 conflict if both contextualizations types appear
        if (os_contextualization.user_data.scheme in obj["schemes"] and
                contextualization.user_data.scheme in obj["schemes"]):
            raise exception.OCCIMixinConflict()

        if os_contextualization.user_data.scheme in obj["schemes"]:
            user_data = attrs.get("org.openstack.compute.user_data")
        if contextualization.user_data.scheme in obj["schemes"]:
            user_data = attrs.get("occi.compute.user_data")

        if (os_contextualization.public_key.scheme in obj["schemes"] and
                contextualization.ssh_key.scheme in obj["schemes"]):
            raise exception.OCCIMixinConflict()

        key_name = key_data = None
        if os_contextualization.public_key.scheme in obj["schemes"]:
            key_name = attrs.get("org.openstack.credentials.publickey.name")
            key_data = attrs.get("org.openstack.credentials.publickey.data")

        if contextualization.ssh_key.scheme in obj["schemes"]:
            if key_data or key_name:
                raise exception.OCCIMixinConflict()
            key_data = attrs.get("occi.credentials.ssh_key")

        if key_name and key_data:
            create_key = True
        elif not key_name and key_data:
            # NOTE(orviz) To be occi-os compliant, not
            # raise exception.MissingKeypairName
            key_name = uuid.uuid4().hex
            create_key = True
            create_key_tmp = True

        if create_key:
            # add keypair: if key_name already exists, a 409 HTTP code
            # will be returned by OpenStack
            self.os_helper.keypair_create(req, key_name,
                                          public_key=key_data)

        block_device_mapping_v2 = self._build_block_mapping(req, obj)
        networks = self._get_network_from_req(req, obj)
        server = self.os_helper.create_server(
            req,
            name,
            image,
            flavor,
            user_data=user_data,
            key_name=key_name,
            block_device_mapping_v2=block_device_mapping_v2,
            networks=networks
        )
        # The returned JSON does not contain the server name
        server["name"] = name
        occi_compute_resources = self._get_compute_resources([server])

        if create_key_tmp:
            self.os_helper.keypair_delete(req, key_name)

        return collection.Collection(resources=occi_compute_resources)

    def show(self, req, id):
        # get info from server
        s = self.os_helper.get_server(req, id)

        # get info from flavor
        flavor = self.os_helper.get_flavor(req, s["flavor"]["id"])
        res_tpl = templates.OpenStackResourceTemplate(flavor["id"],
                                                      flavor["name"],
                                                      flavor["vcpus"],
                                                      flavor["ram"],
                                                      flavor["disk"])

        # get info from image
        img_id = s["image"]["id"]
        try:
            image = self.os_helper.get_image(req, img_id)
        except webob.exc.HTTPNotFound:
            image = {
                "id": img_id,
                "name": "None (Image with ID '%s' not found)" % img_id,
            }

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
        vols = self.os_helper.get_server_volumes_link(req, s["id"])
        for v in vols:
            st = storage.StorageResource(title="storage", id=v["volumeId"])
            comp.add_link(storage_link.StorageLink(comp, st,
                                                   deviceid=v.get("device",
                                                                  None)))

        # network links
        addresses = s.get("addresses", {})
        if addresses:
            for addr_set in addresses.values():
                for addr in addr_set:
                    # TODO(jorgesece): add pool information
                    if addr["OS-EXT-IPS:type"] == "floating":
                        net_id = self.os_helper.get_floatingip_id(
                            req, addr['addr']
                        )
                    else:
                        try:
                            net_id = self.os_helper.get_network_id(
                                req, addr['OS-EXT-IPS-MAC:mac_addr'], id
                            )
                        except webob.exc.HTTPNotFound:
                            net_id = "FIXED"
                    comp.add_link(_create_network_link(
                        addr, comp, net_id,
                        addr["OS-EXT-IPS:type"]))

        return comp

    def _get_server_floating_ips(self, req, server_id):
        s = self.os_helper.get_server(req, server_id)
        addresses = s.get("addresses", {})
        floating_ips = []
        if addresses:
            for addr_set in addresses.values():
                for addr in addr_set:
                    if addr["OS-EXT-IPS:type"] == "floating":
                        floating_ips.append(addr["addr"])
        return floating_ips

    def _release_floating_ips(self, req, server_id):
        server_ips = self._get_server_floating_ips(req, server_id)
        if server_ips:
            floating_ips = self.os_helper.get_floating_ips(req)
            for server_ip in server_ips:
                for ip in floating_ips:
                    if server_ip == ip["ip"]:
                        self.os_helper.remove_floating_ip(req, server_id,
                                                          ip["ip"])

    def _delete(self, req, server_ids):
        for server_id in server_ids:
            self._release_floating_ips(req, server_id)
            self.os_helper.delete(req, server_id)
        return []

    def delete(self, req, id):
        return self._delete(req, [id])

    def delete_all(self, req):
        ids = [s["id"] for s in self.os_helper.index(req)]
        return self._delete(req, ids)
