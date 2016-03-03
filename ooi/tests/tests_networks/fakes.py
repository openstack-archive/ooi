# -*- coding: utf-8 -*-

# Copyright 2015 LIP - Lisbon
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

from ooi import wsgi

application_url = "https://foo.example.org:8774/ooiv1"

tenants = {
    "foo": {"id": uuid.uuid4().hex,
            "name": "foo"},
    "bar": {"id": uuid.uuid4().hex,
            "name": "bar"},
}

subnets = [
    {
        "id": 1,
        "name": "private-subnet",
        "cidr": "33.0.0.1/24",
        "ip_version": "IPv4",
        "gateway_ip": "33.0.0.1",
    },
    {
        "id": 2,
        "name": "public-subnet",
        "cidr": "44.0.0.1/24",
        "ip_version": "IPv4",
        "gateway_ip": "44.0.0.1",
    },
]

networks = {
    tenants["bar"]["id"]: [],
    tenants["foo"]["id"]: [
        {
            "id": uuid.uuid4().hex,
            "name": "foo",
            "subnet_info": subnets[0],
            "status": "ACTIVE",
        },
        {
            "id": uuid.uuid4().hex,
            "name": "bar",
            "subnet_info": subnets[1],
            "status": "SHUTOFF",
        },
    ]
}


def create_fake_json_resp(data, status=200):
    r = webob.Response()
    r.headers["Content-Type"] = "application/json"
    r.charset = "utf8"
    r.body = json.dumps(data).encode("utf8")
    r.status_code = status
    return r


def add_to_fake_json_resp(req, obj_name, data):

    body = json.loads(req.body)
    for element in data:
        body[obj_name].append(element)

    req.body = json.dumps(body).encode("utf8")

    return req


def create_req_test(params, schemes):
    headers = create_header(params, schemes)
    req = webob.Request.blank(path="")
    req.headers = headers
    return wsgi.Request(req.environ)


def create_header(params, schemes, project=None):
    headers = {}
    att = ""
    if params is not None:
        for k, v in params.items():
            att = "%s, %s=%s " % (att, k, v)
        headers["X_OCCI_Attribute"] = att
    if schemes is not None:
        sch = ""
        cat = ""
        for k, v in schemes.items():
            sch = "%s, %s:%s" % (sch, k, v)
            cat = "%s, %s%s" % (cat, k, v)
        headers["schemes"] = sch
        # headers['category']= cat
    if project is not None:
        headers["X_PROJECT_ID"] = project
    return headers