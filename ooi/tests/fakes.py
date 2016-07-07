# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
# Copyright 2015 LIP - INDIGO-DataCloud
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
import re
import uuid

import webob.dec
import webob.exc

from ooi import utils
import ooi.wsgi


application_url = "https://foo.example.org:8774/ooiv1"

tenants = {
    "foo": {"id": uuid.uuid4().hex,
            "name": "foo"},
    "bar": {"id": uuid.uuid4().hex,
            "name": "bar"},
    "baz": {"id": uuid.uuid4().hex,
            "name": "baz"},
}

flavors = {
    1: {
        "id": 1,
        "name": "foo",
        "vcpus": 2,
        "ram": 256,
        "disk": 10,
    },
    2: {
        "id": 2,
        "name": "bar",
        "vcpus": 4,
        "ram": 2014,
        "disk": 20,
    }
}

images = {
    "foo": {
        "id": "foo",
        "name": "foo",
    },
    "bar": {
        "id": "bar",
        "name": "bar",
    }
}

volumes = {
    tenants["foo"]["id"]: [
        {
            "id": uuid.uuid4().hex,
            "displayName": "foo",
            "size": 2,
            "status": "available",
            "attachments": [],
        },
        {
            "id": uuid.uuid4().hex,
            "displayName": "bar",
            "size": 3,
            "status": "available",
            "attachments": [],
        },
        {
            "id": uuid.uuid4().hex,
            "displayName": "baz",
            "size": 5,
            "status": "available",
            "attachments": [],
        },
    ],
    tenants["bar"]["id"]: [],
    tenants["baz"]["id"]: [
        {
            "id": uuid.uuid4().hex,
            "displayName": "volume",
            "size": 5,
            "status": "in-use",
        },
    ],
}

pools = {
    tenants["foo"]["id"]: [
        {
            "id": "foo",
            "name": "foo",
        },
        {
            "id": "bar",
            "name": "bar",
        }
    ],
    tenants["bar"]["id"]: [],
    tenants["baz"]["id"]: [
        {
            "id": "public",
            "name": "public",
        },
    ],
}

linked_vm_id = uuid.uuid4().hex

allocated_ip = "192.168.253.23"

floating_ips = {
    tenants["foo"]["id"]: [],
    tenants["bar"]["id"]: [],
    tenants["baz"]["id"]: [
        {
            "fixed_ip": "10.0.0.2",
            "id": uuid.uuid4().hex,
            "instance_id": linked_vm_id,
            "ip": "192.168.253.1",
            "pool": pools[tenants["baz"]["id"]][0]["name"],
        },
        {
            "fixed_ip": None,
            "id": uuid.uuid4().hex,
            "instance_id": None,
            "ip": "192.168.253.2",
            "pool": pools[tenants["baz"]["id"]][0]["name"],
        },
    ],
}

networks = {
    tenants["foo"]["id"]: [],
    tenants["bar"]["id"]: [],
    tenants["baz"]["id"]: [
        {"id": uuid.uuid4().hex},
        {"id": uuid.uuid4().hex}
        ]
}

ports = {
    tenants["foo"]["id"]: [
        {
            "port_id": uuid.uuid4().hex,
            "fixed_ips":
                [{"ip_address": uuid.uuid4().hex}],
            "mac_addr": uuid.uuid4().hex,
            "port_state": "DOWN",
            "net_id": uuid.uuid4().hex,
            "server_id": linked_vm_id
        },
    ],
    tenants["bar"]["id"]: [],
    tenants["baz"]["id"]: [
        {
            "port_id": uuid.uuid4().hex,
            "fixed_ips": [
                {"ip_address": "192.168.253.1"}
            ],
            "mac_addr": uuid.uuid4().hex,
            "port_state": "ACTIVE",
            "net_id": uuid.uuid4().hex,
            "server_id": linked_vm_id
        },

    ],
}

servers = {
    tenants["foo"]["id"]: [
        {
            "id": uuid.uuid4().hex,
            "name": "foo",
            "flavor": {"id": flavors[1]["id"]},
            "image": {"id": images["foo"]["id"]},
            "status": "ACTIVE",
        },
        {
            "id": uuid.uuid4().hex,
            "name": "bar",
            "flavor": {"id": flavors[2]["id"]},
            "image": {"id": images["bar"]["id"]},
            "status": "SHUTOFF",
        },
        {
            "id": uuid.uuid4().hex,
            "name": "baz",
            "flavor": {"id": flavors[1]["id"]},
            "image": {"id": images["bar"]["id"]},
            "status": "ERROR",
        },
    ],
    tenants["bar"]["id"]: [],
    tenants["baz"]["id"]: [
        {
            "id": linked_vm_id,
            "name": "withvolume",
            "flavor": {"id": flavors[1]["id"]},
            "image": {"id": images["bar"]["id"]},
            "status": "ACTIVE",
            "os-extended-volumes:volumes_attached": [
                {"id": volumes[tenants["baz"]["id"]][0]["id"]}
            ],
            "addresses": {
                "private": [
                    {"addr": (
                        (ports[tenants["baz"]["id"]]
                         [0]["fixed_ips"][0]["ip_address"])
                    ),
                        "OS-EXT-IPS:type": "fixed",
                        "OS-EXT-IPS-MAC:mac_addr": (
                            ports[tenants["baz"]["id"]][0]["mac_addr"]
                        )
                    },
                    {"addr": floating_ips[tenants["baz"]["id"]][0]["ip"],
                     "OS-EXT-IPS:type": "floating",
                     "OS-EXT-IPS-MAC:mac_addr": "1234"},
                ]
            }
        }
    ],
}

# avoid circular definition of attachments
volumes[tenants["baz"]["id"]][0]["attachments"] = [{
    # how consistent can OpenStack be!
    # depending on using /servers/os-volume_attachments
    # or /os-volumes it will return different field names
    "server_id": servers[tenants["baz"]["id"]][0]["id"],
    "serverId": servers[tenants["baz"]["id"]][0]["id"],
    "attachment_id": uuid.uuid4().hex,
    "volumeId": volumes[tenants["baz"]["id"]][0]["id"],
    "volume_id": volumes[tenants["baz"]["id"]][0]["id"],
    "device": "/dev/vdb",
    "id": volumes[tenants["baz"]["id"]][0]["id"],
}]


def fake_query_results():
    cats = []
    # OCCI Core
    cats.append(
        'link; '
        'scheme="http://schemas.ogf.org/occi/core#"; '
        'class="kind"; title="link"; '
        'location="%s/link/"' % application_url)
    cats.append(
        'resource; '
        'scheme="http://schemas.ogf.org/occi/core#"; '
        'class="kind"; title="resource"; '
        'rel="http://schemas.ogf.org/occi/core#entity"; '
        'location="%s/resource/"' % application_url)
    cats.append(
        'entity; '
        'scheme="http://schemas.ogf.org/occi/core#"; '
        'class="kind"; title="entity"; '
        'location="%s/entity/"' % application_url)

    # OCCI Infrastructure Compute
    cats.append(
        'compute; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"; title="compute resource"; '
        'rel="http://schemas.ogf.org/occi/core#resource"; '
        'location="%s/compute/"' % application_url)
    cats.append(
        'start; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"; title="start compute instance"')
    cats.append(
        'stop; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"; title="stop compute instance"')
    cats.append(
        'restart; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"; title="restart compute instance"')
    cats.append(
        'suspend; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"; title="suspend compute instance"')

    # OCCI Templates
    cats.append(
        'os_tpl; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="mixin"; title="OCCI OS Template"; '
        'location="%s/os_tpl/"' % application_url)
    cats.append(
        'resource_tpl; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="mixin"; title="OCCI Resource Template"; '
        'location="%s/resource_tpl/"' % application_url)

    # OpenStack Images
    cats.append(
        'bar; '
        'scheme="http://schemas.openstack.org/template/os#"; '
        'class="mixin"; title="bar"; '
        'rel="http://schemas.ogf.org/occi/infrastructure#os_tpl"; '
        'location="%s/os_tpl/bar"' % application_url)
    cats.append(
        'foo; '
        'scheme="http://schemas.openstack.org/template/os#"; '
        'class="mixin"; title="foo"; '
        'rel="http://schemas.ogf.org/occi/infrastructure#os_tpl"; '
        'location="%s/os_tpl/foo"' % application_url)

    # OpenStack Flavors
    cats.append(
        '1; '
        'scheme="http://schemas.openstack.org/template/resource#"; '
        'class="mixin"; title="Flavor: foo"; '
        'rel="http://schemas.ogf.org/occi/infrastructure#resource_tpl"; '
        'location="%s/resource_tpl/1"' % application_url)
    cats.append(
        '2; '
        'scheme="http://schemas.openstack.org/template/resource#"; '
        'class="mixin"; title="Flavor: bar"; '
        'rel="http://schemas.ogf.org/occi/infrastructure#resource_tpl"; '
        'location="%s/resource_tpl/2"' % application_url)

    # OCCI Infrastructure Network
    cats.append(
        'network; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"; title="network resource"; '
        'rel="http://schemas.ogf.org/occi/core#resource"; '
        'location="%s/network/"' % application_url)
    cats.append(
        'ipnetwork; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/network#"; '
        'class="mixin"; title="IP Networking Mixin"')
    cats.append(
        'up; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/network/action#"; '
        'class="action"; title="up network instance"')
    cats.append(
        'down; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/network/action#"; '
        'class="action"; title="down network instance"')
    cats.append(
        'networkinterface; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"; title="network link resource"; '
        'rel="http://schemas.ogf.org/occi/core#link"; '
        'location="%s/networklink/"' % application_url)
    cats.append(
        'ipnetworkinterface; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/'
        'networkinterface#"; '
        'class="mixin"; title="IP Network interface Mixin"')

    # OCCI Infrastructure Storage
    cats.append(
        'storage; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"; title="storage resource"; '
        'rel="http://schemas.ogf.org/occi/core#resource"; '
        'location="%s/storage/"' % application_url)
    cats.append(
        'storagelink; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"; title="storage link resource"; '
        'rel="http://schemas.ogf.org/occi/core#link"; '
        'location="%s/storagelink/"' % application_url)
    cats.append(
        'offline; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"; title="offline storage instance"')
    cats.append(
        'online; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"; title="online storage instance"')
    cats.append(
        'backup; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"; title="backup storage instance"')
    cats.append(
        'resize; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"; title="resize storage instance"')
    cats.append(
        'snapshot; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"; title="snapshot storage instance"')

    # OpenStack contextualization
    cats.append(
        'user_data; '
        'scheme="http://schemas.openstack.org/compute/instance#"; '
        'class="mixin"; title="Contextualization extension - user_data"')
    cats.append(
        'public_key; '
        'scheme="http://schemas.openstack.org/instance/credentials#"; '
        'class="mixin"; title="Contextualization extension - public_key"')

    result = []
    for c in cats:
        result.append(("Category", c))
    return result


class FakeOpenStackFault(ooi.wsgi.Fault):
    _fault_names = {
        400: "badRequest",
        401: "unauthorized",
        403: "forbidden",
        404: "itemNotFound",
        405: "badMethod",
        406: "notAceptable",
        409: "conflictingRequest",
        413: "overLimit",
        415: "badMediaType",
        429: "overLimit",
        501: "notImplemented",
        503: "serviceUnavailable"}

    @webob.dec.wsgify()
    def __call__(self, req):
        code = self.wrapped_exc.status_int
        fault_name = self._fault_names.get(code)
        explanation = self.wrapped_exc.explanation
        fault_data = {
            fault_name: {
                'code': code,
                'message': explanation}}
        self.wrapped_exc.body = utils.utf8(json.dumps(fault_data))
        self.wrapped_exc.content_type = "application/json"
        return self.wrapped_exc


class FakeApp(object):
    """Poor man's fake application."""

    def __init__(self):
        self.routes = {}

        for tenant in tenants.values():
            path = "/%s" % tenant["id"]

            self._populate(path, "server", servers[tenant["id"]], actions=True)
            self._populate(path, "volume", volumes[tenant["id"]], "os-volumes")
            self._populate(path, "floating_ip_pool", pools[tenant["id"]],
                           "os-floating-ip-pools")
            self._populate(path, "floating_ip", floating_ips[tenant["id"]],
                           "os-floating-ips")
            self._populate_ports(path, servers[tenant["id"]],
                                 ports[tenant["id"]])
            # NOTE(aloga): dict_values un Py3 is not serializable in JSON
            self._populate(path, "image", list(images.values()))
            self._populate(path, "flavor", list(flavors.values()))
            self._populate_attached_volumes(path, servers[tenant["id"]],
                                            volumes[tenant["id"]])

    def _populate(self, path_base, obj_name, obj_list,
                  objs_path=None, actions=[]):
        objs_name = "%ss" % obj_name
        if objs_path:
            path = "%s/%s" % (path_base, objs_path)
        else:
            path = "%s/%s" % (path_base, objs_name)
        objs_details_path = "%s/detail" % path
        self.routes[path] = create_fake_json_resp({objs_name: obj_list})
        self.routes[objs_details_path] = create_fake_json_resp(
            {objs_name: obj_list})

        for o in obj_list:
            obj_path = "%s/%s" % (path, o["id"])
            self.routes[obj_path] = create_fake_json_resp({obj_name: o})

            if actions:
                action_path = "%s/action" % obj_path
                self.routes[action_path] = webob.Response(status=202)

    def _populate_attached_volumes(self, path, server_list, vol_list):
        for s in server_list:
            attachments = []
            if "os-extended-volumes:volumes_attached" in s:
                for attach in s["os-extended-volumes:volumes_attached"]:
                    for v in vol_list:
                        if attach["id"] == v["id"]:
                            attachments.append(v["attachments"][0])
            path_base = "%s/servers/%s/os-volume_attachments" % (path, s["id"])
            self.routes[path_base] = create_fake_json_resp(
                {"volumeAttachments": attachments}
            )
            for attach in attachments:
                obj_path = "%s/%s" % (path_base, attach["id"])
                self.routes[obj_path] = create_fake_json_resp(
                    {"volumeAttachment": attach})

    def _populate_ports(self, path, servers_list, ports_list):
        if servers_list:
            for p in ports_list:
                path_base = "%s/servers/%s/%s" % (
                    path,
                    servers_list[0]["id"],
                    "os-interface"
                )
                self.routes[path_base] = create_fake_json_resp(
                    {"interfaceAttachments": [p]})

    @webob.dec.wsgify()
    def __call__(self, req):
        if req.method == "GET":
            return self._do_get(req)
        elif req.method == "POST":
            return self._do_post(req)
        elif req.method == "DELETE":
            return self._do_delete(req)

    def _do_create_server(self, req):
        # TODO(enolfc): this should check the json is
        # semantically correct
        s = {"server": {"id": "foo",
                        "name": "foo",
                        "flavor": {"id": "1"},
                        "image": {"id": "2"},
                        "status": "ACTIVE"}}
        return create_fake_json_resp(s)

    def _do_create_volume(self, req):
        # TODO(enolfc): this should check the json is
        # semantically correct
        s = {"volume": {"id": "foo",
                        "displayName": "foo",
                        "size": 1,
                        "status": "on-line"}}
        return create_fake_json_resp(s)

    def _do_create_attachment(self, req):
        v = {"volumeAttachment": {"serverId": "foo",
                                  "volumeId": "bar",
                                  "device": "/dev/vdb"}}
        return create_fake_json_resp(v, 202)

    def _do_allocate_ip(self, req):
        tenant = req.path_info.split('/')[1]
        body = req.json_body.copy()
        pool = body.popitem()
        if pool[1]:
            for p in pools[tenant]:
                if p["name"] == pool[1]:
                    break
            else:
                exc = webob.exc.HTTPNotFound()
                return FakeOpenStackFault(exc)
        ip = {"floating_ip": {"ip": allocated_ip, "id": 1}}
        return create_fake_json_resp(ip, 202)

    def _do_create_port(self, req):
        req_content = req.path_info.split('/')
        tenant = req_content[1]
        server = req_content[3]
        body = req.json_body.copy()
        net = body["interfaceAttachment"]["net_id"]
        port = ports[tenant]
        p = {"interfaceAttachment": {
            "port_id": uuid.uuid4().hex,
            "fixed_ips":
                [{"ip_address":
                    port[0]["fixed_ips"]
                    [0]["ip_address"]
                  }],
            "mac_addr": port[0]["mac_addr"],
            "port_state": "DOWN",
            "net_id": net,
            "server_id": server
        }}
        return create_fake_json_resp(p, 200)

    def _do_post(self, req):
        if req.path_info.endswith("servers"):
            return self._do_create_server(req)
        if req.path_info.endswith("os-volumes"):
            return self._do_create_volume(req)
        elif req.path_info.endswith("action"):
            body = req.json_body.copy()
            action = body.popitem()
            if action[0] in ["os-start", "os-stop", "reboot",
                             "addFloatingIp", "removeFloatingIp"]:
                return self._get_from_routes(req)
        elif req.path_info.endswith("os-volume_attachments"):
            return self._do_create_attachment(req)
        elif req.path_info.endswith("os-floating-ips"):
            return self._do_allocate_ip(req)
        elif req.path_info.endswith("os-interface"):
            return self._do_create_port(req)
        raise Exception

    def _do_delete(self, req):
        self._do_get(req)
        tested_paths = {
            r"/[^/]+/servers/[^/]+/os-volume_attachments/[^/]+$": 202,
            r"/[^/]+/os-floating-ips/[^/]+$": 202,
            r"/[^/]+/servers/[^/]+$": 204,
            r"/[^/]+/os-volumes/[^/]+$": 204,
            r"/[^/]+/servers/[^/]+/os-interface/[^/]+$": 204,
        }
        for p, st in tested_paths.items():
            if re.match(p, req.path_info):
                return create_fake_json_resp({}, st)
        raise Exception

    def _do_get(self, req):
        return self._get_from_routes(req)

    def _get_from_routes(self, req):
        try:
            ret = self.routes[req.path_info]
        except KeyError:
            exc = webob.exc.HTTPNotFound()
            ret = FakeOpenStackFault(exc)
        return ret


def create_fake_json_resp(data, status=200):
    r = webob.Response()
    r.headers["Content-Type"] = "application/json"
    r.charset = "utf8"
    r.body = json.dumps(data).encode("utf8")
    r.status_code = status
    return r
