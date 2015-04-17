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
            "id": uuid.uuid4().hex,
            "name": "withvolume",
            "flavor": {"id": flavors[1]["id"]},
            "image": {"id": images["bar"]["id"]},
            "status": "ACTIVE",
            "os-extended-volumes:volumes_attached": [
                {"id": volumes[tenants["baz"]["id"]][0]["id"]}
            ]
        },
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
    cats.append(
        'storage; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"')
    cats.append(
        'storagelink; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"')
    cats.append(
        'compute; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="kind"')
    cats.append(
        'link; '
        'scheme="http://schemas.ogf.org/occi/core#"; '
        'class="kind"')
    cats.append(
        'resource; '
        'scheme="http://schemas.ogf.org/occi/core#"; '
        'class="kind"')
    cats.append(
        'entity; '
        'scheme="http://schemas.ogf.org/occi/core#"; '
        'class="kind"')
    cats.append(
        'offline; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"')
    cats.append(
        'online; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"')
    cats.append(
        'backup; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"')
    cats.append(
        'resize; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"')
    cats.append(
        'snapshot; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/storage/action#"; '
        'class="action"')
    cats.append(
        'start; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"')
    cats.append(
        'stop; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"')
    cats.append(
        'restart; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"')
    cats.append(
        'suspend; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; '
        'class="action"')
    cats.append(
        'bar; '
        'scheme="http://schemas.openstack.org/template/os#"; '
        'class="mixin"')
    cats.append(
        'bar; '
        'scheme="http://schemas.openstack.org/template/resource#"; '
        'class="mixin"')
    cats.append(
        'foo; '
        'scheme="http://schemas.openstack.org/template/os#"; '
        'class="mixin"')
    cats.append(
        'foo; '
        'scheme="http://schemas.openstack.org/template/resource#"; '
        'class="mixin"')
    cats.append(
        'os_tpl; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="mixin"')
    cats.append(
        'resource_tpl; '
        'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
        'class="mixin"')
    cats.append(
        'user_data; '
        'scheme="http://schemas.openstack.org/compute/instance#"; '
        'class="mixin"')
    cats.append(
        'public_key; '
        'scheme="http://schemas.openstack.org/instance/credentials#"; '
        'class="mixin"')

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

    def _do_create_attachment(self, req):
        v = {"volumeAttachment": {"serverId": "foo",
                                  "volumeId": "bar",
                                  "device": "/dev/vdb"}}
        return create_fake_json_resp(v, 202)

    def _do_post(self, req):
        if req.path_info.endswith("servers"):
            return self._do_create_server(req)
        elif req.path_info.endswith("action"):
            body = req.json_body.copy()
            action = body.popitem()
            if action[0] in ["os-start", "os-stop", "reboot"]:
                return self._get_from_routes(req)
        elif req.path_info.endswith("os-volume_attachments"):
            return self._do_create_attachment(req)
        raise Exception

    def _do_delete(self, req):
        self._do_get(req)
        if "os-volume_attachments" in req.path_info:
            return create_fake_json_resp({}, 202)
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
