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

#  {
#    "networks": [
#        {
#            "status": "ACTIVE",
#            "subnets": [
#                "54d6f61d-db07-451c-9ab3-b9609b6b6f0b"
#            ],
#            "name": "private-network",
#            "provider:physical_network": null,
#            "admin_state_up": true,
#            "tenant_id": "4fd44f30292945e481c7b8a0c8908869",
#            "provider:network_type": "local",
#            "router:external": true,
#            "shared": true,
#            "id": "d32019d3-bc6e-4319-9c1d-6722fc136a22",
#            "provider:segmentation_id": null
#        },
#       ...
#  }

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
            "subnets": [subnets[0]["id"]],
            "status": "ACTIVE",
        },
        {
            "id": uuid.uuid4().hex,
            "name": "bar",
            "subnets": [subnets[1]["id"]],
            "status": "SHUTOFF",
        },
    ]
}


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
            path = ""
            self._populate(path, "network", networks[tenant["id"]],tenant_id=tenant["id"], actions=True)

    def _populate(self, path_base, obj_name, obj_list, tenant_id,
                  objs_path=None, actions=[]):
        objs_name = "%ss" % obj_name
        if objs_path:
            path = "%s/%s" % (path_base, objs_path)
        else:
            path = "%s/%s" % (path_base, objs_name)
        if path in self.routes:
            self.routes[path] = add_to_fake_json_resp(self.routes[path], objs_name, obj_list)
        else:
            self.routes[path] = create_fake_json_resp({objs_name: obj_list})

        path_by_tenant = "%s?tenant_id=%s" % (path, tenant_id)
        self.routes[path_by_tenant] = create_fake_json_resp({objs_name: obj_list})

        for net in obj_list:
            objs_details_path = "%s/%s" % (path, net['id'])
            self.routes[objs_details_path] = create_fake_json_resp({obj_name: net})

        for o in obj_list: #this maybe is not necessary. ID path is created in the previous lines.
            obj_path = "%s?%s_id=%s" % (path, obj_name, o["id"])
            self.routes[obj_path] = create_fake_json_resp({obj_name: o})

            if actions:
                action_path = "%s/action" % obj_path
                self.routes[action_path] = webob.Response(status=202)

    @webob.dec.wsgify()
    def __call__(self, req):
        if req.method == "GET":
            return self._do_get(req)
        elif req.method == "POST":
            return self._do_post(req)
      #  if req.method == "POST":
      #      return self._do_create_network(req)

    def _do_post(self, req):
        if req.path_info.endswith("networks"):
            return self._do_create_network(req)
        elif req.path_info.endswith("action"):
            body = req.json_body.copy()
            action = body.popitem()
            if action[0] in ["os-start", "os-stop"]:
                return self._get_from_routes(req)
        raise Exception

    def _do_create_network(self, req):
        # TODO(enolfc): this should check the json is
        # semantically correct
        s = {"network": {"id": "foo",
                        "name": "foo",
                        "flavor": {"id": "1"},
                        "image": {"id": "2"},
                        "status": "ACTIVE"}}
        return create_fake_json_resp(s)

    def _do_create_subnet(self, req):
        # TODO(enolfc): this should check the json is
        # semantically correct
        s = {"volume": {"id": "foo",
                        "displayName": "foo",
                        "size": 1,
                        "status": "on-line"}}
        return create_fake_json_resp(s)

    def _do_get(self, req):
        return self._get_from_routes(req)

    def _get_from_routes(self, req):
        try:
            if req.query_string:
                ret = self.routes[req.path_info + "?" + req.query_string]
            else:
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


def add_to_fake_json_resp(req, obj_name, data):

    body = json.loads(req.body)
    for element in data:
        body[obj_name].append(element)

    req.body = json.dumps(body).encode("utf8")

    return  req

