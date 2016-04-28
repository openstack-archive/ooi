# -*- coding: utf-8 -*-

# Copyright 2016 LIP - Lisbon
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

import copy
import json

import webob.exc

from ooi.api import helpers
from ooi import exception
from ooi.openstack import helpers as os_helpers
from ooi import utils


class OpenStackNeutron(helpers.BaseHelper):
    """Class to interact with the neutron API."""

    def __init__(self, neutron_endpoint):
        super(OpenStackNeutron, self).__init__(None, None)
        self.neutron_endpoint = neutron_endpoint

    translation = {
        "networks": {"occi.core.title": "name",
                     "occi.core.id": "network_id",
                     "occi.network.state": "status",
                     "org.openstack.network.public": "router:external",
                     "org.openstack.network.shared": "shared",
                     "X_PROJECT_ID": "tenant_id",
                     },
        "subnets": {"occi.core.id": "network_id",
                    "org.openstack.network.ip_version": "ip_version",
                    "occi.network.address": "cidr",
                    "occi.network.gateway": "gateway_ip"
                    },
        "networks_link": {"occi.core.target": "network_id",
                          "occi.core.source": "device_id",
                          },
    }
    required = {"networks": {"occi.core.title": "name",
                             "occi.network.address": "cidr",
                             }
                }

    @staticmethod
    def _build_link(net_id, compute_id, ip, mac=None, pool=None,
                    state='active'):
        link = {}
        link['mac'] = mac
        link['pool'] = pool
        link['network_id'] = net_id
        link['compute_id'] = compute_id
        link['ip'] = ip
        link['state'] = state
        return link

    @staticmethod
    def _build_networks(networks):
        ooi_net_list = []
        for net in networks:
            ooi_net = {}
            status = net.get("status", None)
            ooi_net["state"] = os_helpers.network_status(status)
            public = net.get('router:external', None)
            if public:
                ooi_net["id"] = 'PUBLIC'
            else:
                ooi_net["id"] = net["id"]
            ooi_net["name"] = net.get("name", None)
            if "subnet_info" in net:
                sub = net["subnet_info"]
                ooi_net["address"] = sub.get("cidr", None)
                ooi_net["ip_version"] = sub.get("ip_version", None)
                ooi_net["gateway"] = sub.get("gateway_ip", None)
            ooi_net_list.append(ooi_net)
        return ooi_net_list

    @staticmethod
    def get_from_response(response, element, default):
        """Get a JSON element from a valid response or raise an exception.

        This method will extract an element a JSON response
         (falling back to a default value) if the response has a code
          of 200, otherwise it will raise a webob.exc.exception

        :param response: The webob.Response object
        :param element: The element to look for in the JSON body
        :param default: The default element to be returned if not found.
        """
        if response.status_int in [200, 201, 202]:
            if element:
                return response.json_body.get(element, default)
            else:
                return response.json_body
        elif response.status_int in [204]:
            return []
        else:
            raise helpers.exception_from_response(response)

    def _get_req(self, req, method,
                 path=None,
                 content_type="application/json",
                 body=None,
                 query_string=""):
        """Return a new Request object to interact with OpenStack.

        This method will create a new request starting with the same WSGI
        environment as the original request, prepared to interact with
        OpenStack. Namely, it will override the script name to match the
        OpenStack version. It will also override the path, content_type and
        body of the request, if any of those keyword arguments are passed.

        :param req: the original request
        :param path: new path for the request
        :param content_type: new content type for the request, defaults to
                             "application/json" if not specified
        :param body: new body for the request
        :param query_string: query string for the request, defaults to an empty
                             query if not specified
        :returns: a Request object
        """
        server = self.neutron_endpoint
        environ = copy.copy(req.environ)
        try:
            if "HTTP_X-Auth-Token" not in environ:
                env_token = req.environ["keystone.token_auth"]
                token = env_token.get_auth_ref(None)['auth_token']
                environ = {"HTTP_X-Auth-Token": token}
        except Exception:
            raise webob.exc.HTTPUnauthorized

        new_req = webob.Request.blank(path=path,
                                      environ=environ, base_url=server)
        new_req.query_string = query_string
        new_req.method = method
        if path is not None:
            new_req.path_info = path
        if content_type is not None:
            new_req.content_type = content_type
        if body is not None:
            new_req.body = utils.utf8(body)

        return new_req

    def _make_get_request(self, req, path, parameters=None):
        """Create GET request

        This method create a GET Request instance

        :param req: the incoming request
        :param path: element location
        :param parameters: parameters to filter results
        :param tenant: include tenant in the query parameters
        """
        query_string = utils.get_query_string(parameters)
        return self._get_req(req, path=path,
                             query_string=query_string, method="GET")

    def _make_create_request(self, req, resource, parameters):
        """Create CREATE request

        This method create a CREATE Request instance

        :param req: the incoming request
        :param parameters: parameters with values
        """
        path = "/%s" % resource
        single_resource = resource[:-1]
        body = utils.make_body(single_resource, parameters)
        return self._get_req(req, path=path,
                             content_type="application/json",
                             body=json.dumps(body), method="POST")

    def _make_delete_request(self, req, path, id):
        """Create DELETE request

        This method create a DELETE Request instance

        :param req: the incoming request
        :param path: element location
        """
        path = "%s/%s" % (path, id)
        return self._get_req(req, path=path, method="DELETE")

    def _make_put_request(self, req, path, parameters):
        """Create DELETE request

        This method create a DELETE Request instance

        :param req: the incoming request
        :param path: element location
        """
        body = utils.make_body(None, parameters)
        return self._get_req(req, path=path,
                             content_type="application/json",
                             body=json.dumps(body), method="PUT")

    def _get_public_network(self, req):
        """Get public network

        This method get public network id

        :param req: the incoming request
        """
        att_public = {"router:external": True}
        net_public = self.list_resources(req,
                                         'networks',
                                         att_public)
        return net_public[0]["id"]

    def list_resources(self, req, resource, parameters):
        """List resources.

        It returns json code from the server

        :param req: the incoming request
        :param resource: network resource to manage
        :param parameters: query parameters
        :param tenant: include tenant in the query parameters
        """
        path = "/%s" % resource
        os_req = self._make_get_request(req, path, parameters)
        response = os_req.get_response()
        return self.get_from_response(response, resource, [])

    def get_resource(self, req, resource, id):
        """Get information from a resource.

        :param req: the incoming request
        :param resource: network resource to manage
        :param id: subnet identification
        """
        path = "/%s/%s" % (resource, id)
        req = self._make_get_request(req, path)
        response = req.get_response()
        single_resource = resource[:-1]
        return self.get_from_response(response, single_resource, {})

    def create_resource(self, req, resource, parameters):
        """Create a resource.

        :param req: the incoming request
        :param resource: network resource to manage
        :param parameters: parameters with values for the new network
        """
        single_resource = resource[:-1]
        req_subnet = self._make_create_request(req, resource, parameters)
        response_subnet = req_subnet.get_response()
        json_response = self.get_from_response(
            response_subnet, single_resource, {})
        return json_response

    def delete_resource(self, req, resource, id):
        """Delete resource. It returns empty array

        :param req: the incoming request
        :param parameters: conain id
        """
        path = "/%s" % resource
        req = self._make_delete_request(req, path, id)
        response = req.get_response()
        return self.get_from_response(response, None, [])

    def _add_router_interface(self, req, router_id, subnet_id):
        """Add interface.

        :param req: the incoming request
        :param router_id: router identification
        :param subnet_id: router identification
        """
        path = "/routers/%s/add_router_interface" % router_id
        parameters = {'subnet_id': subnet_id}
        os_req = self._make_put_request(req, path, parameters)
        response = os_req.get_response()
        json_response = self.get_from_response(
            response, None, {})
        return json_response

    def _remove_router_interface(self, req, router_id, port_id):
        """Remove interface.

        :param req: the incoming request
        :param router_id: router identification
        :param subnet_id: router identification
        """
        path = "/routers/%s/remove_router_interface" % router_id
        parameters = {'port_id': port_id}
        os_req = self._make_put_request(req, path, parameters)
        response = os_req.get_response()
        json_response = self.get_from_response(
            response, None, {})
        return json_response

    def create_port(self, req, parameters):
        """Add a port to the subnet

        Returns the port information

        :param req: the incoming network
        :param parameters: list of parameters
        """
        param_device_owner = {'device_owner': 'compute:nova'}
        attributes_port = utils.translate_parameters(
            self.translation['networks_link'],
            parameters)
        attributes_port.update(param_device_owner)
        p = self.create_resource(req,
                                 'ports',
                                 attributes_port)
        link = self._build_link(
            p["network_id"],
            p['device_id'],
            p["fixed_ips"][0]["ip_address"],
            mac=p["mac_address"],
            state=os_helpers.network_status(p["status"]))
        return link

    def delete_port(self, req, iface):
        """Delete a port to the subnet

        Returns the port information

        :param req: the incoming network
        :param iface: link information
        """
        mac = iface['mac']
        attributes_port = {
            "mac_address": mac
        }
        ports = self.list_resources(
            req,
            'ports', attributes_port
        )
        if ports.__len__() == 0:
            raise exception.LinkNotFound(
                "Interface %s not found" % mac
            )
        out = self.delete_resource(req,
                                   'ports',
                                   ports[0]['id'])
        return out

    def get_network_id(self, req, mac, server_id=None):
        """Get the Network ID from the mac port

        :param req: the incoming network
        :param mac: mac port
        :param server_id: id not use in neutron
        """
        try:
            attributes_port = {
                "mac_address": mac
            }
            ports = self.list_resources(
                req,
                'ports', attributes_port
            )
            id = ports[0]['network_id']
        except Exception:
            raise exception.NetworkNotFound
        return id

    def _add_floating_ip(self, req, public_net_id, port_id):
        """Add floating to the public network and a port

        Creates the floating IP and asign it to the port
        of the device.

        :param req: the incoming network
        :param public_net_id: public network id
        :param port_id: port id of the device
        """
        attributes_port = {
            "floating_network_id": public_net_id,
            "port_id": port_id
        }
        floating_ip = self.create_resource(req,
                                           'floatingips',
                                           attributes_port)
        return floating_ip

    def _remove_floating_ip(self, req, public_net_id, ip):
        """Delete floating to the public network and a port

        Delete the floating IP and asign it to the port
        of the device.

        :param req: the incoming network
        :param public_net_id: network id
        :param ip: floating ip to remove
        """
        attributes_port = {
            "floating_network_id": public_net_id,
            "floating_ip_address": ip
        }
        try:
            floating_ip = self.list_resources(req,
                                              'floatingips',
                                              attributes_port)
            response = self.delete_resource(req,
                                            'floatingips',
                                            floating_ip[0]['id'])
        except Exception:
            raise exception.NotFound
        return response

    def get_network_details(self, req, id):
        """Get info from a network.

        It returns json code from the server

        :param req: the incoming network
        :param id: net identification
        """
        path = "/networks/%s" % id
        req = self._make_get_request(req, path)
        response = req.get_response()
        net = self.get_from_response(response, "network", {})
        # subnet
        if "subnets" in net:
            path = "/subnets/%s" % net["subnets"][0]
            req_subnet = self._make_get_request(req, path)
            response_subnet = req_subnet.get_response()
            net["subnet_info"] = self.get_from_response(
                response_subnet, "subnet", {})

        ooi_networks = self._build_networks([net])

        return ooi_networks[0]

    def index(self, req, parameters):
        """List networks.

        It returns json code from the server

        :param req: the incoming request
        :param parameters: query parameters
        """
        param = utils.translate_parameters(
            self.translation['networks'], parameters)
        networks = self.list_resources(req,
                                       'networks',
                                       param)
        ooi_networks = self._build_networks(networks)
        return ooi_networks

    def create_network(self, req, parameters):
        """Create a full neutron network.

        It creates a private network conected to the public one.
        It creates a full network objects stack:
        network, subnet, port, and router.
        In case of error, the objects already created are deleted.

        :param req: the incoming request
        :param resource: network resource to manage
        :param parameters: parameters with values
         for the new network
        """
        # NETWORK
        net_param = utils.translate_parameters(
            self.translation['networks'], parameters)
        net = self.create_resource(req,
                                   'networks',
                                   net_param)
        # SUBNETWORK
        try:
            subnet_param = utils.translate_parameters(
                self.translation['subnets'], parameters)

            subnet_param["network_id"] = net["id"]
            net["subnet_info"] = self.create_resource(
                req, 'subnets', subnet_param)

        # INTERFACE and ROUTER information is agnostic to the user
            net_public = self._get_public_network(req)
            attributes_router = {"external_gateway_info": {
                "network_id": net_public}
            }
            router = self.create_resource(req,
                                          'routers',
                                          attributes_router)
            try:
                # create interface to the network
                self._add_router_interface(req,
                                           router['id'],
                                           net['subnet_info']['id']
                                           )
            except Exception as ex:
                self.delete_resource(req,
                                     'routers',
                                     router['id']
                                     )
                raise ex
        except Exception as ex:
            self.delete_resource(req,
                                 'networks', net['id'])
            raise ex
        ooi_net = self._build_networks([net])
        return ooi_net[0]

    def delete_network(self, req, id, parameters=None):
        """Delete a full network.

        :param req: the incoming request
        :param id: net identification
        :param parameters: parameters
        """
        param = {"network_id": id}
        ports = self.list_resources(req, 'ports', param)
        for port in ports:
            if port['device_owner'] == "network:router_interface":
                self._remove_router_interface(req,
                                              port['device_id'],
                                              port['id'],
                                              )
                self.delete_resource(req,
                                     'routers', port["device_id"])
            else:
                self.delete_resource(req,
                                     'ports', port["id"])
        response = self.delete_resource(req,
                                        'networks',
                                        id)
        return response

    def assign_floating_ip(self, req, parameters):
        """assign floating ip to a server

        :param req: the incoming request
        :param paramet: network and compute identification
        """
        # net_id it is not needed if
        # there is just one port of the VM
        attributes_port = utils.translate_parameters(
            self.translation['networks_link'],
            parameters)
        attributes_port.pop('network_id')
        try:
            net_public = self._get_public_network(req)
        except Exception:
            raise exception.NetworkNotFound()
        try:
            ports = self.list_resources(req, 'ports', attributes_port)
            port_id = ports[0]['id']
            # subnet_id = ports[0]['fixed_ips'][0]['subnet_id']
        except Exception:
            raise exception.NotFound()
        response = self._add_floating_ip(req, net_public, port_id)
        try:
            link_public = self._build_link(
                ports[0]['network_id'],
                attributes_port['device_id'],
                response['floating_ip_address'],
                pool=response['floating_network_id'])
        except Exception:
            raise exception.OCCIInvalidSchema()
        return link_public

    def release_floating_ip(self, req, iface):
        """release floating ip from a server

        :param req: the incoming request
        :param iface: link information
        """
        # net_id it is not needed if there is just one port of the VM
        try:
            net_public = self._get_public_network(req)
        except Exception:
            raise exception.NetworkNotFound()
        response = self._remove_floating_ip(req, net_public, iface['ip'])

        return response

    def list_compute_net_links(self, req, parameters=None):
        """List the network and compute links

        It lists every private and public ip related to
        the servers of the tenant

        :param req: the incoming request
        :param parameters: the incoming parameters
        """
        # net_id it is not needed if
        # there is just one port of the VM
        param_port = {'device_owner': 'compute:nova'}
        param_common = utils.translate_parameters(
            self.translation['networks_link'], parameters)

        param_port.update(param_common)
        link_list = []
        try:
            ports = self.list_resources(req, 'ports', param_port)
            for port in ports:
                link_private = self._build_link(
                    port["network_id"],
                    port['device_id'],
                    port["fixed_ips"][0]["ip_address"],
                    mac=port["mac_address"],
                    state=os_helpers.network_status(port["status"]))
                link_list.append(link_private)
                # Query public links associated to the port
                floating_ips = self.list_resources(req,
                                                   'floatingips',
                                                   {"port_id": port['id']})
                for f_ip in floating_ips:
                    link_public = self._build_link(
                        port["network_id"],
                        port['device_id'],
                        f_ip['floating_ip_address'],
                        pool=f_ip['floating_network_id'])
                    # FIXME(jorgesece) could be port mac
                    link_list.append(link_public)
        except Exception:
            raise exception.NotFound()
        return link_list

    def get_compute_net_link(self, req, compute_id, network_id,
                             ip, parameters=None):
        """Get a specific network/server link

        It shows a specific link (either private or public ip)

        :param req: the incoming request
        :param compute_id: server id
        :param network_id: network id
        :param ip: ip connected
        :param parameters: the incoming parameters
        """
        try:
            if network_id == "PUBLIC":
                param = {'floating_ip_address': ip}
                flo_ips = self.list_resources(req,
                                              'floatingips',
                                              param)
                for f_ip in flo_ips:
                    link_public = self._build_link(
                        network_id,
                        compute_id,
                        f_ip['floating_ip_address'],
                        pool=f_ip['floating_network_id'])
                    return link_public
            else:
                param_ports = {'device_id': compute_id,
                               'network_id': network_id}
                ports = self.list_resources(req, 'ports', param_ports)
                for p in ports:
                    if ip == p["fixed_ips"][0]["ip_address"]:
                        link_private = self._build_link(
                            p["network_id"],
                            p['device_id'],
                            p["fixed_ips"][0]["ip_address"],
                            mac=p["mac_address"],
                            state=os_helpers.network_status(p["status"]))
                        return link_private
            raise exception.NotFound()
        except Exception:
            raise exception.NotFound()

    def run_action(self, req, action, net_id):
        """Run an action on a network.

        :param req: the incoming request
        :param action: the action to run
        :param net_id: server id to delete
        """
        os_req = self._make_action_reques(req, action, id)
        response = os_req.get_response()
        if response.status_int != 202:
            raise helpers.exception_from_response(response)
