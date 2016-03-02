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

import ooi.wsgi
from ooi import utils

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
#address=s["subnet_info"]["cidr"],ip_version=s["subnet_info"]["ip_version"], gateway=s["subnet_info"]["gateway_ip"]
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

#
# def fake_query_results():
#     cats = []
#     # OCCI Core
#     cats.append(
#         'link; '
#         'scheme="http://schemas.ogf.org/occi/core#"; '
#         'class="kind"; title="link"; '
#         'location="%s/link/"' % application_url)
#     cats.append(
#         'resource; '
#         'scheme="http://schemas.ogf.org/occi/core#"; '
#         'class="kind"; title="resource"; '
#         'rel="http://schemas.ogf.org/occi/core#entity"; '
#         'location="%s/resource/"' % application_url)
#     cats.append(
#         'entity; '
#         'scheme="http://schemas.ogf.org/occi/core#"; '
#         'class="kind"; title="entity"; '
#         'location="%s/entity/"' % application_url)
#
#
#
#     # OCCI Templates
#     cats.append(
#         'os_tpl; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
#         'class="mixin"; title="OCCI OS Template"; '
#         'location="%s/os_tpl/"' % application_url)
#     cats.append(
#         'resource_tpl; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
#         'class="mixin"; title="OCCI Resource Template"; '
#         'location="%s/resource_tpl/"' % application_url)
#
#     # OpenStack Images
#     cats.append(
#         'bar; '
#         'scheme="http://schemas.openstack.org/template/os#"; '
#         'class="mixin"; title="bar"; '
#         'rel="http://schemas.ogf.org/occi/infrastructure#os_tpl"; '
#         'location="%s/os_tpl/bar"' % application_url)
#     cats.append(
#         'foo; '
#         'scheme="http://schemas.openstack.org/template/os#"; '
#         'class="mixin"; title="foo"; '
#         'rel="http://schemas.ogf.org/occi/infrastructure#os_tpl"; '
#         'location="%s/os_tpl/foo"' % application_url)
#
#     # OpenStack Flavors
#     cats.append(
#         '1; '
#         'scheme="http://schemas.openstack.org/template/resource#"; '
#         'class="mixin"; title="Flavor: foo"; '
#         'rel="http://schemas.ogf.org/occi/infrastructure#resource_tpl"; '
#         'location="%s/resource_tpl/1"' % application_url)
#     cats.append(
#         '2; '
#         'scheme="http://schemas.openstack.org/template/resource#"; '
#         'class="mixin"; title="Flavor: bar"; '
#         'rel="http://schemas.ogf.org/occi/infrastructure#resource_tpl"; '
#         'location="%s/resource_tpl/2"' % application_url)
#
#     # OCCI Infrastructure Network
#     cats.append(
#         'network; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
#         'class="kind"; title="network resource"; '
#         'rel="http://schemas.ogf.org/occi/core#resource"; '
#         'location="%s/network/"' % application_url)
#     cats.append(
#         'ipnetwork; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure/network#"; '
#         'class="mixin"; title="IP Networking Mixin"')
#     cats.append(
#         'up; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure/network/action#"; '
#         'class="action"; title="up network instance"')
#     cats.append(
#         'down; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure/network/action#"; '
#         'class="action"; title="down network instance"')
#     cats.append(
#         'networkinterface; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure#"; '
#         'class="kind"; title="network link resource"; '
#         'rel="http://schemas.ogf.org/occi/core#link"; '
#         'location="%s/networklink/"' % application_url)
#     cats.append(
#         'ipnetworkinterface; '
#         'scheme="http://schemas.ogf.org/occi/infrastructure/'
#         'networkinterface#"; '
#         'class="mixin"; title="IP Network interface Mixin"')
#
#
#
#     # OpenStack contextualization
#     cats.append(
#         'user_data; '
#         'scheme="http://schemas.openstack.org/compute/instance#"; '
#         'class="mixin"; title="Contextualization extension - user_data"')
#     cats.append(
#         'public_key; '
#         'scheme="http://schemas.openstack.org/instance/credentials#"; '
#         'class="mixin"; title="Contextualization extension - public_key"')
#
#     result = []
#     for c in cats:
#         result.append(("Category", c))
#     return result
from ooi.wsgi import Request

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

    return  req

def create_req_test(params, schemes):
    headers = create_header(params,schemes)
    req = webob.Request.blank(path="")
    req.headers = headers
    return Request(req.environ)

def create_header(params, schemes, project=None):
    headers = {}
    att = ""
    if params:
        for k,v in params.iteritems():
            att = "%s, %s=%s " % (att,k,v)
        headers["X_OCCI_Attribute"]= att
    if schemes:
        sch = ""
        cat = ""
        for k,v in schemes.iteritems():
            sch = "%s, %s:%s" % (sch, k,v)
            cat = "%s, %s%s" % (cat, k,v)
        headers["schemes"] = sch
        #headers['category']= cat
    if project:
        headers["X_PROJECT_ID"]=project
    return headers