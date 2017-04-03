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
import uuid

import six
import webob.dec
import webob.exc

from ooi.api import network
from ooi.api import network_link
from ooi import wsgi


application_url = "https://foo.example.org:8774/ooiv1"

tenants = {
    "foo": {"id": uuid.uuid4().hex,
            "name": "foo"},
    "baz": {"id": uuid.uuid4().hex,
            "name": "foo"},
    "bar": {"id": uuid.uuid4().hex,
            "name": "bar"},
    "public": {"id": uuid.uuid4().hex,
               "name": "bar"},
}

subnets = [
    {
        "id": uuid.uuid4().hex,
        "name": "private-subnet",
        "cidr": "33.0.0.1/24",
        "ip_version": 4,
        "gateway_ip": "33.0.0.1",
    },
    {
        "id": uuid.uuid4().hex,
        "name": "public-subnet",
        "cidr": "44.0.0.1/24",
        "ip_version": 4,
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
            "status": "DOWN",
        },
    ]
}

networks_nova = {
    tenants["bar"]["id"]: [],
    tenants["foo"]["id"]: [
        {
            "id": uuid.uuid4().hex,
            "label": "foo",
            "gateway": "33.0.0.1",
            "cidr": "33.0.0.1/24",
            "status": "ACTIVE",
        },
        {
            "id": uuid.uuid4().hex,
            "label": "bar",
            "gateway": "44.0.0.1",
            "cidr": "44.0.0.1/24",
            "status": "DOWN",
        },
    ]
}

pools = {
    tenants["bar"]["id"]: [],
    tenants["foo"]["id"]: [
        {
            "id": uuid.uuid4().hex,
            "name": "foo",
        },
        {
            "id": uuid.uuid4().hex,
            "name": "bar",
        },
    ]
}

linked_vm_id = uuid.uuid4().hex
linked_net_id = uuid.uuid4().hex

allocated_ip = "192.168.253.23"

ports = {
    tenants["foo"]["id"]: [
        {"id": uuid.uuid4().hex,
         "device_id": uuid.uuid4().hex,
         "device_owner": uuid.uuid4().hex
         }
    ]
}

network_links = {
    tenants["bar"]["id"]: [],
    tenants["foo"]["id"]: [
        {
            "ip": "10.0.0.2",
            "id": uuid.uuid4().hex,
            "instance_id": linked_vm_id,
            "ip": "192.168.253.1",
            "network_id": linked_net_id,
            "pool": pools[tenants["foo"]["id"]][0]["name"],
            'status':'active'
        },
        {
            "ip": None,
            "id": uuid.uuid4().hex,
            "instance_id": None,
            "network_id": linked_net_id,
            "ip": "192.168.253.2",
            "pool": pools[tenants["foo"]["id"]][0]["name"],
            'status':'inactive'
        },
    ],
    tenants["public"]["id"]: [
        {
            "ip": "10.0.0.2",
            "id": uuid.uuid4().hex,
            "instance_id": linked_vm_id,
            "ip": "192.168.253.1",
            "network_id": 'PUBLIC',
            "pool": pools[tenants["foo"]["id"]][0]["name"],
            'status': 'active'
        },
    ],
}

security_groups = {
    tenants["bar"]["id"]: [],
    tenants["foo"]["id"]: [],
    tenants["baz"]["id"]: [
        {
            "name": "group1",
            "id": uuid.uuid4().hex,
            "description": "group one",
            "security_group_rules": [
                {"ethertype": "IPv4", "port_range_min": 443,
                 "port_range_max": 443, "remote_ip_prefix": "10.0.0.0/32",
                 "protocol": "tcp", "direction": "ingress"},
                {"ethertype": "IPv4", "port_range_min": "8000",
                 "port_range_max": 9000, "remote_ip_prefix": "11.0.0.0/24",
                 "protocol": "udp", "direction": "egress"}
            ]
        },
        {
            "name": "group2",
            "id": uuid.uuid4().hex,
            "description": "group two",
            "security_group_rules": [
                {"ethertype": "IPv4", "port_range_min": 80,
                 "port_range_max": 80, "remote_ip_prefix": "10.0.0.0/32",
                 "protocol": "tcp", "direction": "ingress"},
                {"ethertype": "IPv4", "port_range_min": "5000",
                 "port_range_max": 6000, "remote_ip_prefix": "11.0.0.0/24",
                 "protocol": "udp", "direction": "egress"}
            ]
        }

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
        # headers['Category']= cat
    if project is not None:
        headers["X_PROJECT_ID"] = project
    return headers


def create_req_json_occi(params, category, method="POST"):
    headers = create_headers(category,
                             content_type="application/occi+json")
    body = {}
    for c in category:
        body["kind"] = "%s%s" % (
            c.scheme, c.term)

    body["attributes"] = params
    req = webob.Request.blank(path="")
    req.headers = headers
    req.method = method
    req.body = json.dumps(body).encode("utf8")
    return wsgi.Request(req.environ)


def create_req_test_occi(params, category):
    headers = create_header_occi(params, category)
    req = webob.Request.blank(path="")
    req.headers = headers
    return wsgi.Request(req.environ)


def create_header_occi(params, category, project=None):
    headers = create_headers(category, project)
    att = ""
    if params is not None:
        for k, v in params.items():
            if isinstance(v, six.string_types):
                att = "%s, %s=\"%s\"" % (att, k, v)
            else:
                att = "%s, %s=%s" % (att, k, v)
        headers["X_OCCI_Attribute"] = att

    return headers


def create_headers(category, content_type=None,
                   project=None):
    headers = {}
    if category is not None:
        cat = ""
        for c in category:
            cat = "%s%s; scheme=%s; class=%s, " % (
                cat,
                c.term, c.scheme, c.occi_class)
        headers['Category'] = cat[:-1]
    if project is not None:
        headers['X_PROJECT_ID'] = project
    if content_type is not None:
        headers['Content-Type'] = content_type
    return headers


def fake_build_link(net_id, compute_id, ip, mac=None,
                    pool=None, state='active', public_ip=False):
    link = {}
    link['mac'] = mac
    link['pool'] = pool
    link['network_id'] = net_id
    link['compute_id'] = compute_id
    link['ip'] = ip
    link['state'] = state
    link['public_ip'] = public_ip
    return link


def fake_network_link_occi(os_list_net):
    list_links = []
    for l in os_list_net:
        if l['instance_id']:
            list_links.append(fake_build_link(l['network_id'],
                                              l['instance_id'], l['ip']))
    return network_link._get_network_link_resources(list_links)


def fake_build_net(name, ip_version=4, address='0.0.0.11', gateway='0.0.0.1',
                   id="33", state='active'):
    link = {}
    link['id'] = id
    link['name'] = name
    link['address'] = address
    link['gateway'] = gateway
    link['ip_version'] = ip_version
    link['state'] = state
    return link


def fake_network_occi(os_list_net):
    list_nets = []
    for n in os_list_net:
        list_nets.append(fake_build_net(n['name'], id=n['id']))
    return network.Controller._get_network_resources(list_nets)


def build_occi_network(network):
    name = network["name"]
    network_id = network["id"]
    subnet_info = network["subnet_info"]
    status = network["status"].upper()
    if status in ("ACTIVE",):
        status = "active"
    else:
        status = "inactive"

    app_url = application_url
    cats = []
    cats.append('network; '
                'scheme='
                '"http://schemas.ogf.org/occi/infrastructure#";'
                ' class="kind"; title="network resource";'
                ' rel='
                '"http://schemas.ogf.org/occi/core#resource";'
                ' location="%s/network/"' % app_url)
    cats.append('ipnetwork; '
                'scheme='
                '"http://schemas.ogf.org/occi/infrastructure/network#";'
                ' class="mixin"; title="IP Networking Mixin"')
    cats.append('osnetwork; '
                'scheme='
                '"http://schemas.openstack.org/infrastructure/network#";'
                ' class="mixin"; title="openstack network"')

    links = []
    links.append('<%s/network/%s?action=up>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#up"' %
                 (application_url, network_id))
    links.append('<%s/network/%s?action=down>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#down"' %
                 (application_url, network_id))

    attrs = [
        'occi.core.id="%s"' % network_id,
        'occi.core.title="%s"' % name,
        'occi.network.state="%s"' % status,
        'org.openstack.network.ip_version=%s' % subnet_info["ip_version"],
        'occi.network.address="%s"' % subnet_info["cidr"],
        'occi.network.gateway="%s"' % subnet_info["gateway_ip"],
        ]
    result = []
    for c in cats:
        result.append(("Category", c))
    for a in attrs:
        result.append(("X-OCCI-Attribute", a))
    for l in links:
        result.append(("Link", l))
    return result


def build_occi_nova(network):
    name = network["label"]
    network_id = network["id"]
    gateway = network["gateway"]
    cidr = network["cidr"]
    status = "active"

    app_url = application_url
    cats = []
    cats.append('network; '
                'scheme='
                '"http://schemas.ogf.org/occi/infrastructure#";'
                ' class="kind"; title="network resource";'
                ' rel='
                '"http://schemas.ogf.org/occi/core#resource";'
                ' location="%s/network/"' % app_url)
    cats.append('ipnetwork; '
                'scheme='
                '"http://schemas.ogf.org/occi/infrastructure/network#";'
                ' class="mixin"; title="IP Networking Mixin"')
    cats.append('osnetwork; '
                'scheme='
                '"http://schemas.openstack.org/infrastructure/network#";'
                ' class="mixin"; title="openstack network"')

    links = []
    links.append('<%s/network/%s?action=up>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#up"' %
                 (application_url, network_id))
    links.append('<%s/network/%s?action=down>; '
                 'rel="http://schemas.ogf.org/occi/'
                 'infrastructure/network/action#down"' %
                 (application_url, network_id))

    attrs = [
        'occi.core.id="%s"' % network_id,
        'occi.core.title="%s"' % name,
        'occi.network.state="%s"' % status,
        'occi.network.address="%s"' % cidr,
        'occi.network.gateway="%s"' % gateway,
        ]
    result = []
    for c in cats:
        result.append(("Category", c))
    for a in attrs:
        result.append(("X-OCCI-Attribute", a))
    for l in links:
        result.append(("Link", l))
    return result


def build_occi_securitygroup(secgroup):
    name = secgroup["title"]
    secgroup_id = secgroup["id"]
    rules = secgroup["rules"]
    summary = secgroup["summary"]
    app_url = application_url
    cats = []
    cats.append('securitygroup; '
                'scheme='
                '"http://schemas.ogf.org/occi/infrastructure#";'
                ' class="kind"; title="securitygroup resource";'
                ' rel='
                '"http://schemas.ogf.org/occi/core#resource";'
                ' location="%s/securitygroup/"' % app_url)
    links = []

    attrs = [
        'occi.core.id="%s"' % secgroup_id,
        'occi.core.title="%s"' % name,
        'occi.core.summary="%s"' % summary,
        'occi.securitygroup.rules="%s"' % json.dumps(rules).replace('"', "'"),
        ]
    result = []
    for c in cats:
        result.append(("Category", c))
    for a in attrs:
        result.append(("X-OCCI-Attribute", a))
    for l in links:
        result.append(("Link", l))
    return result