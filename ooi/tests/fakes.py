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


tenants = {
    "foo": {"id": uuid.uuid4().hex,
            "name": "foo"},
    "bar": {"id": uuid.uuid4().hex,
            "name": "bar"}
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
}


def fake_query_results():
    cats = []
    cats.append(
        'start; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; '
        'class="action"')
    cats.append(
        'stop; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; '
        'class="action"')
    cats.append(
        'restart; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; '
        'class="action"')
    cats.append(
        'suspend; '
        'scheme="http://schemas.ogf.org/occi/infrastructure/compute/action"; '
        'class="action"')

    result = []
    for c in cats:
        result.append(("Category", c))
    return result


class FakeApp(object):
    """Poor man's fake application."""

    def __init__(self):
        self.routes = {}

        for tenant in tenants.values():
            path = "/%s" % tenant["id"]

            self._populate(path, "server", servers[tenant["id"]])
            # NOTE(aloga): dict_values un Py3 is not serializable in JSON
            self._populate(path, "image", list(images.values()))
            self._populate(path, "flavor", list(flavors.values()))

    def _populate(self, path_base, obj_name, obj_list):
        objs_name = "%ss" % obj_name
        objs_path = "%s/%s" % (path_base, objs_name)
        self.routes[objs_path] = create_fake_json_resp({objs_name: obj_list})

        for o in obj_list:
            obj_path = "%s/%s" % (objs_path, o["id"])
            self.routes[obj_path] = create_fake_json_resp({obj_name: o})

    @webob.dec.wsgify()
    def __call__(self, req):
        if req.method == "GET":
            return self._do_get(req)
        elif req.method == "POST":
            return self._do_post(req)

    def _do_create(self, req):
        s = {"server": {"id": "foo",
                        "name": "foo",
                        "flavor": {"id": "1"},
                        "image": {"id": "2"},
                        "status": "ACTIVE"}}
        return create_fake_json_resp(s)

    def _do_post(self, req):
        if req.path_info.endswith("servers"):
            return self._do_create(req)
        raise Exception

    def _do_get(self, req):
        try:
            ret = self.routes[req.path_info]
        except Exception:
            raise
        return ret


def create_fake_json_resp(data):
    r = webob.Response()
    r.headers["Content-Type"] = "application/json"
    r.charset = "utf8"
    r.body = json.dumps(data).encode("utf8")
    return r
