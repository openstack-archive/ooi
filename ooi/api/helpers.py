# -*- coding: utf-8 -*-

# Copyright 2015 Spanish National Research Council
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
import os

import six.moves.urllib.parse as urlparse

from ooi import exception
from ooi.log import log as logging
from ooi.openstack import helpers as os_helpers
from ooi import utils

import webob.exc

LOG = logging.getLogger(__name__)


def _resolve_id(base_url, resource_url):
    """Gets the resource id from a base URL.

    :param base_url: application or request url (normally absolute)
    :param resource_url: absolute or relative resource url
    :returns: a tuple with the calculated base url and resource id
    """
    if not base_url.endswith('/'):
        base_url = base_url + '/'
    full_url = urlparse.urljoin(base_url, resource_url)
    parts = urlparse.urlsplit(full_url)
    base_parts = parts[0:2] + (os.path.dirname(parts[2]),) + parts[3:]
    return urlparse.urlunsplit(base_parts), os.path.basename(parts[2])


def get_id_with_kind(req, resource_url, kind=None):
    """Resolves the resource URL and tries to match it with the kind.

    :param req: current request
    :param resource_url: absolute or relative resource url
    :returns: a tuple with a base url and a resource id
    :raises ooi.exception.Invalid: if resource does not match kind
    """
    res_base, res_id = _resolve_id(req.url, resource_url)
    if kind:
        kind_base, kind_id = _resolve_id(req.application_url, kind.location)
        if kind_base != res_base:
            raise exception.Invalid("Expecting %s resource" % kind_base)
    return res_base, res_id


def exception_from_response(response):
    """Convert an OpenStack V2 Fault into a webob exception.

    Since we are calling the OpenStack API we should process the Faults
    produced by them. Extract the Fault information according to [1] and
    convert it back to a webob exception.

    [1] http://docs.openstack.org/developer/nova/v2/faults.html

    :param response: a webob.Response containing an exception
    :returns: a webob.exc.exception object
    """
    exceptions = {
        400: webob.exc.HTTPBadRequest,
        401: webob.exc.HTTPUnauthorized,
        403: webob.exc.HTTPForbidden,
        404: webob.exc.HTTPNotFound,
        405: webob.exc.HTTPMethodNotAllowed,
        406: webob.exc.HTTPNotAcceptable,
        409: webob.exc.HTTPConflict,
        413: webob.exc.HTTPRequestEntityTooLarge,
        415: webob.exc.HTTPUnsupportedMediaType,
        429: webob.exc.HTTPTooManyRequests,
        501: webob.exc.HTTPNotImplemented,
        503: webob.exc.HTTPServiceUnavailable,
    }
    code = response.status_int
    exc = exceptions.get(code, webob.exc.HTTPInternalServerError)
    try:
        message = response.json_body.popitem()[1].get("message")
        exc = exc(explanation=message)
    except Exception:
        LOG.exception("Unknown error happenened processing response %s"
                      % response)
        return webob.exc.HTTPInternalServerError()
    return exc


class BaseHelper(object):
    """Base helper to interact with nova API."""
    def __init__(self, app, openstack_version):
        self.app = app
        self.openstack_version = openstack_version

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
        if hasattr(self, 'neutron_endpoint'):
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
        else:
            new_req = webob.Request(copy.copy(req.environ))
            new_req.script_name = self.openstack_version
        new_req.query_string = query_string
        new_req.method = method
        if path is not None:
            new_req.path_info = path
        if content_type is not None:
            new_req.content_type = content_type
        if body is not None:
            new_req.body = utils.utf8(body)
        return new_req

    @staticmethod
    def get_from_response(response, element, default):
        """Get a JSON element from a valid response or raise an exception.

        This method will extract an element a JSON response (falling back to a
        default value) if the response has a code of 200, otherwise it will
        raise a webob.exc.exception

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
            raise exception_from_response(response)

    def _make_get_request(self, req, path, parameters=None):
        """Create GET request

        This method creates a GET Request instance

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

        This method creates a CREATE Request instance

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

        This method creates a DELETE Request instance

        :param req: the incoming request
        :param path: element location
        """
        path = "%s/%s" % (path, id)
        return self._get_req(req, path=path, method="DELETE")

    def _make_put_request(self, req, path, parameters):
        """Create DELETE request

        This method creates a DELETE Request instance

        :param req: the incoming request
        :param path: element location
        """
        body = utils.make_body(None, parameters)
        return self._get_req(req, path=path,
                             content_type="application/json",
                             body=json.dumps(body), method="PUT")


class OpenStackHelper(BaseHelper):
    """Class to interact with the nova API."""
    required = {"networks": {"occi.core.title": "label",
                             "occi.network.address": "cidr",
                             }
                }

    @staticmethod
    def tenant_from_req(req):
        try:
            return req.environ["HTTP_X_PROJECT_ID"]
        except KeyError:
            raise exception.Forbidden(reason="Cannot find project ID")

    def _get_index_req(self, req):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers" % tenant_id
        return self._get_req(req, path=path, method="GET")

    def index(self, req):
        """Get a list of servers for a tenant.

        :param req: the incoming request
        """
        os_req = self._get_index_req(req)
        response = os_req.get_response(self.app)
        return self.get_from_response(response, "servers", [])

    def _get_delete_req(self, req, server_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers/%s" % (tenant_id, server_id)
        return self._get_req(req, path=path, method="DELETE")

    def delete(self, req, server_id):
        """Delete a server.

        :param req: the incoming request
        :param server_id: server id to delete
        """
        os_req = self._get_delete_req(req, server_id)
        response = os_req.get_response(self.app)
        # FIXME(aloga): this should be handled in get_from_response, shouldn't
        # it?
        if response.status_int not in [204]:
            raise exception_from_response(response)

    def _get_run_action_req(self, req, action, server_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers/%s/action" % (tenant_id, server_id)

        actions_map = {
            "stop": {"os-stop": None},
            "start": {"os-start": None},
            "suspend": {"suspend": None},
            "resume": {"resume": None},
            "unpause": {"unpause": None},
            "restart": {"reboot": {"type": "SOFT"}},
        }
        action = actions_map[action]

        body = json.dumps(action)
        return self._get_req(req, path=path, body=body, method="POST")

    def run_action(self, req, action, server_id):
        """Run an action on a server.

        :param req: the incoming request
        :param action: the action to run
        :param server_id: server id to delete
        """
        os_req = self._get_run_action_req(req, action, server_id)
        response = os_req.get_response(self.app)
        if response.status_int != 202:
            raise exception_from_response(response)

    def _get_server_req(self, req, server_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers/%s" % (tenant_id, server_id)
        return self._get_req(req, path=path, method="GET")

    def get_server(self, req, server_id):
        """Get info from a server.

        :param req: the incoming request
        :param server_id: server id to get info from
        """
        req = self._get_server_req(req, server_id)
        response = req.get_response(self.app)
        return self.get_from_response(response, "server", {})

    def _get_create_server_req(self, req, name, image, flavor,
                               user_data=None,
                               key_name=None,
                               block_device_mapping_v2=None,
                               networks=None):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers" % tenant_id
        # TODO(enolfc): add here the correct metadata info
        # if contextualization.public_key.scheme in obj["schemes"]:
        #     req_body["metadata"] = XXX
        body = {"server": {
            "name": name,
            "imageRef": image,
            "flavorRef": flavor,
        }}
        if user_data is not None:
            body["server"]["user_data"] = user_data
        if key_name is not None:
            body["server"]["key_name"] = key_name
        if block_device_mapping_v2:
            body["server"]["block_device_mapping_v2"] = block_device_mapping_v2
        if networks:
            body["server"]["networks"] = networks

        return self._get_req(req,
                             path=path,
                             content_type="application/json",
                             body=json.dumps(body),
                             method="POST")

    def create_server(self, req, name, image, flavor,
                      user_data=None, key_name=None,
                      block_device_mapping_v2=None,
                      networks=None):
        """Create a server.

        :param req: the incoming request
        :param name: name for the new server
        :param image: image id for the new server
        :param flavor: flavor id for the new server
        :param user_data: user data to inject into the server
        :param key_name: user public key name
        """
        req = self._get_create_server_req(
            req,
            name,
            image,
            flavor,
            user_data=user_data,
            key_name=key_name,
            block_device_mapping_v2=block_device_mapping_v2,
            networks=networks)
        response = req.get_response(self.app)
        # We only get one server
        return self.get_from_response(response, "server", {})

    def _get_flavors_req(self, req):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/flavors/detail" % tenant_id
        return self._get_req(req, path=path, method="GET")

    def get_flavors(self, req):
        """Get information from all flavors.

        :param req: the incoming request
        """
        req = self._get_flavors_req(req)
        response = req.get_response(self.app)
        return self.get_from_response(response, "flavors", [])

    def _get_flavor_req(self, req, flavor_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/flavors/%s" % (tenant_id, flavor_id)
        return self._get_req(req, path=path, method="GET")

    def get_flavor(self, req, flavor_id):
        """Get information from a flavor.

        :param req: the incoming request
        :param flavor_id: flavor id to get info from
        """
        req = self._get_flavor_req(req, flavor_id)
        response = req.get_response(self.app)
        return self.get_from_response(response, "flavor", {})

    def _get_images_req(self, req):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/images/detail" % tenant_id
        return self._get_req(req, path=path, method="GET")

    def get_images(self, req):
        """Get information from all images.

        :param req: the incoming request
        """
        req = self._get_images_req(req)
        response = req.get_response(self.app)
        return self.get_from_response(response, "images", [])

    def _get_image_req(self, req, image_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/images/%s" % (tenant_id, image_id)
        return self._get_req(req, path=path, method="GET")

    def get_image(self, req, image_id):
        """Get information from an image.

        :param req: the incoming request
        :param image_id: image id to get info from
        """
        req = self._get_image_req(req, image_id)
        response = req.get_response(self.app)
        return self.get_from_response(response, "image", {})

    def _get_volumes_req(self, req):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-volumes" % tenant_id
        return self._get_req(req, path=path, method="GET")

    def get_volumes(self, req):
        req = self._get_volumes_req(req)
        response = req.get_response(self.app)
        return self.get_from_response(response, "volumes", [])

    def _get_volume_req(self, req, volume_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-volumes/%s" % (tenant_id, volume_id)
        return self._get_req(req, path=path, method="GET")

    def get_volume(self, req, volume_id):
        """Get information from a volume.

        :param req: the incoming request
        :param volume_id: volume id to get info from
        """
        req = self._get_volume_req(req, volume_id)
        response = req.get_response(self.app)
        return self.get_from_response(response, "volume", [])

    def _get_server_volumes_link_req(self, req, server_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers/%s/os-volume_attachments" % (tenant_id, server_id)
        return self._get_req(req, path=path, method="GET")

    def get_server_volumes_link(self, req, server_id):
        """Get volumes attached to a server.

        :param req: the incoming request
        :param server_id: server id to get volumes from
        """
        req = self._get_server_volumes_link_req(req, server_id)
        response = req.get_response(self.app)
        return self.get_from_response(response, "volumeAttachments", [])

    def _get_server_volumes_link_create_req(self, req, s_id, v_id, dev=None):
        tenant_id = self.tenant_from_req(req)
        body = {
            "volumeAttachment": {
                "volumeId": v_id
            }
        }
        if dev is not None:
            body["volumeAttachment"]["device"] = dev
        path = "/%s/servers/%s/os-volume_attachments" % (tenant_id, s_id)
        return self._get_req(req,
                             path=path,
                             content_type="application/json",
                             body=json.dumps(body),
                             method="POST")

    def create_server_volumes_link(self, req, server_id, vol_id, dev=None):
        req = self._get_server_volumes_link_create_req(req, server_id, vol_id,
                                                       dev=dev)
        response = req.get_response(self.app)
        return self.get_from_response(response, "volumeAttachment", {})

    def _get_server_volumes_link_delete_req(self, req, server_id, vol_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers/%s/os-volume_attachments/%s" % (tenant_id,
                                                            server_id, vol_id)
        return self._get_req(req, path=path, method="DELETE")

    def delete_server_volumes_link(self, req, server_id, vol_id):
        req = self._get_server_volumes_link_delete_req(req, server_id, vol_id)
        response = req.get_response(self.app)
        if response.status_int not in [202]:
            raise exception_from_response(response)

    def _get_floating_ips_req(self, req):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-floating-ips" % tenant_id
        return self._get_req(req, path=path, method="GET")

    def get_floating_ips(self, req):
        """Get floating IPs for the tenant.

        :param req: the incoming request
        """
        req = self._get_floating_ips_req(req)
        response = req.get_response(self.app)
        return self.get_from_response(response, "floating_ips", [])

    def _get_floating_ip_pools_req(self, req):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-floating-ip-pools" % tenant_id
        return self._get_req(req, path=path, method="GET")

    def get_floating_ip_pools(self, req):
        """Get floating IP pools for the tenant.

        :param req: the incoming request
        """
        req = self._get_floating_ip_pools_req(req)
        response = req.get_response(self.app)
        return self.get_from_response(response, "floating_ip_pools", [])

    def _get_volume_delete_req(self, req, vol_id):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-volumes/%s" % (tenant_id, vol_id)
        return self._get_req(req, path=path, method="DELETE")

    def volume_delete(self, req, vol_id):
        """Delete a volume.

        :param req: the incoming request
        :param vol_id: volume id to delete
        """
        req = self._get_volume_delete_req(req, vol_id)
        response = req.get_response(self.app)
        # FIXME(aloga): this should be handled in get_from_response, shouldn't
        # it?
        if response.status_int not in [204]:
            raise exception_from_response(response)

    def _get_volume_create_req(self, req, name, size):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-volumes" % tenant_id
        body = {"volume": {
            "display_name": name,
            "size": size,
        }}
        return self._get_req(req,
                             path=path,
                             content_type="application/json",
                             body=json.dumps(body),
                             method="POST")

    def volume_create(self, req, name, size):
        """Create a volume.

        :param req: the incoming request
        :param name: name for the new volume
        :param size: size for the new volume
        """
        req = self._get_volume_create_req(req, name, size)
        response = req.get_response(self.app)
        # We only get one volume
        return self.get_from_response(response, "volume", {})

    def _get_floating_ip_allocate_req(self, req, pool=None):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-floating-ips" % tenant_id
        body = {"pool": pool}
        return self._get_req(req, path=path, body=json.dumps(body),
                             method="POST")

    def allocate_floating_ip(self, req, pool=None):
        """Allocate a floating ip from a pool.

        :param req: the incoming request
        :param pool: floating ip pool to get the IP from
        """
        req = self._get_floating_ip_allocate_req(req, pool)
        response = req.get_response(self.app)
        return self.get_from_response(response, "floating_ip", {})

    def _get_floating_ip_release_req(self, req, ip):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-floating-ips/%s" % (tenant_id, ip)
        return self._get_req(req, path=path, method="DELETE")

    def release_floating_ip(self, req, ip):
        """Release a floating ip.

        :param req: the incoming request
        :param ip: floating ip pool to release
        """
        req = self._get_floating_ip_release_req(req, ip)
        response = req.get_response(self.app)
        if response.status_int != 202:
            raise exception_from_response(response)

    def _get_associate_floating_ip_req(self, req, server, address):
        tenant_id = self.tenant_from_req(req)
        body = {"addFloatingIp": {"address": address}}
        path = "/%s/servers/%s/action" % (tenant_id, server)
        return self._get_req(req, path=path, body=json.dumps(body),
                             method="POST")

    def associate_floating_ip(self, req, server, address):
        """Associate a floating ip to a server.

        :param req: the incoming request
        :param server: the server to associate the ip to
        :param address: ip to associate to the server
        """
        req = self._get_associate_floating_ip_req(req, server, address)
        response = req.get_response(self.app)
        if response.status_int != 202:
            raise exception_from_response(response)

    def _get_remove_floating_ip_req(self, req, server, address):
        tenant_id = self.tenant_from_req(req)
        body = {"removeFloatingIp": {"address": address}}
        path = "/%s/servers/%s/action" % (tenant_id, server)
        return self._get_req(req, path=path, body=json.dumps(body),
                             method="POST")

    def remove_floating_ip(self, req, server, address):
        """Remove a floating ip to a server.

        :param req: the incoming request
        :param server: the server to remove the ip from
        :param address: ip to remove from the server
        """
        req = self._get_remove_floating_ip_req(req, server, address)
        response = req.get_response(self.app)
        if response.status_int != 202:
            raise exception_from_response(response)

    def _get_keypair_create_req(self, req, name, public_key=None):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-keypairs" % tenant_id
        body = {"keypair": {
            "name": name,
        }}
        if public_key:
            body["keypair"]["public_key"] = public_key

        return self._get_req(req,
                             path=path,
                             content_type="application/json",
                             body=json.dumps(body),
                             method="POST")

    def keypair_create(self, req, name, public_key=None):
        """Create a keypair.

        :param req: the incoming request
        :param name: name for the new keypair
        :param public_key: public ssh key to import
        """
        req = self._get_keypair_create_req(req, name, public_key=public_key)
        response = req.get_response(self.app)
        return self.get_from_response(response, "keypair", {})

    def _get_keypair_delete_req(self, req, name):
        tenant_id = self.tenant_from_req(req)
        path = "/%s/os-keypairs/%s" % (tenant_id, name)
        return self._get_req(req, path=path, method="DELETE")

    def keypair_delete(self, req, name):
        """Delete a keypair.

        :param req: the incoming request
        :param name: keypair name to delete
        """
        req = self._get_keypair_delete_req(req, name)
        response = req.get_response(self.app)
        # FIXME(orviz) API says 204 is the normal response code but it
        # is actually returning 202 (bug likely)
        if response.status_int not in [202, 204]:
            raise exception_from_response(response)

    @staticmethod
    def _build_link(net_id, compute_id, ip, ip_id=None, mac=None, pool=None,
                    state='ACTIVE'):
        link = {}
        link['mac'] = mac
        link['pool'] = pool
        link['network_id'] = net_id
        link['compute_id'] = compute_id
        link['ip'] = ip
        link['ip_id'] = ip_id
        link['state'] = os_helpers.vm_state(state)
        return link

    def _get_ports(self, req, compute_id):
        result = []
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers/%s/os-interface" % (tenant_id, compute_id)
        os_req = self._get_req(req, path=path, method="GET")
        response = os_req.get_response(self.app)
        try:
            result = self.get_from_response(response,
                                            "interfaceAttachments", [])
        except Exception as e:
            LOG.exception("Interfaces can not be shown: " + e.explanation)
        return result

    def get_compute_net_link(self, req, compute_id, network_id,
                             address):
        """Get a specific network/server link

        It shows a specific link (either private or public ip)

        :param req: the incoming request
        :param compute_id: server id
        :param network_id: network id
        :param address: ip connected
        """

        s = self.get_server(req, compute_id)
        pool = None
        ip_id = None
        server_addrs = s.get("addresses", {})
        for addr_set in server_addrs.values():
            for addr in addr_set:
                if addr["addr"] == address:
                    mac = addr["OS-EXT-IPS-MAC:mac_addr"]
                    if network_id == os_helpers.PUBLIC_NETWORK:
                        floating_ips = self.get_floating_ips(
                            req
                        )
                        for ip in floating_ips:
                            if address == ip['ip']:
                                pool = ip['pool']
                                ip_id = ip['id']
                    else:
                        ports = self._get_ports(req, compute_id)
                        for p in ports:
                            if p["net_id"] == network_id:
                                for ip in p["fixed_ips"]:
                                    if ip['ip_address'] == address:
                                        ip_id = p['port_id']
                    return self._build_link(network_id,
                                            compute_id,
                                            address,
                                            mac=mac,
                                            pool=pool,
                                            ip_id=ip_id
                                            )
        raise exception.NotFound()

    def list_compute_net_links(self, req):
        """Get floating IPs for the tenant.

        :param req: the incoming request
        """
        floating_ips = self.get_floating_ips(req)
        float_list = {}
        for ip in floating_ips:
            if ip["instance_id"]:
                float_list.update({ip['fixed_ip']: ip})
        servers = self.index(req)
        link_list = []
        for s in servers:
            ports = self._get_ports(req, s['id'])
            for p in ports:
                for ip in p["fixed_ips"]:
                    mac = p['mac_addr']
                    state = p["port_state"]
                    link = self._build_link(p["net_id"],
                                            s['id'],
                                            ip['ip_address'],
                                            ip_id=p["port_id"],
                                            mac=mac,
                                            state=state)
                    link_list.append(link)
                    float_ip = float_list.get(ip['ip_address'], None)
                    if float_ip:
                        link = self._build_link(p["net_id"],
                                                float_ip['instance_id'],
                                                float_ip['ip'],
                                                ip_id=float_ip["id"],
                                                mac=mac,
                                                pool=float_ip["pool"]
                                                )
                        link_list.append(link)
        if not link_list:
            for ip in floating_ips:
                link = self._build_link(os_helpers.PUBLIC_NETWORK,
                                        ip['instance_id'],
                                        ip['ip'],
                                        ip_id=ip["id"],
                                        pool=ip["pool"]
                                        )
                link_list.append(link)
        return link_list

    def create_port(self, req, network_id, device_id):
        """Add a port to the subnet

        Returns the port information

        :param req: the incoming network
        :param network_id: network id
        :param device_id: device id
        """
        param_port = {
            'net_id': network_id,
            'server_id': device_id
        }
        compute_id = param_port.get("server_id")
        tenant_id = self.tenant_from_req(req)
        path = "/%s/servers/%s/os-interface" % (tenant_id, compute_id)
        body = utils.make_body("interfaceAttachment", param_port)
        os_req = self._get_req(req, path=path,
                               content_type="application/json",
                               body=json.dumps(body), method="POST")
        response = os_req.get_response(self.app)
        port = self.get_from_response(response, "interfaceAttachment", {})
        for ip in port["fixed_ips"]:
            return self._build_link(port["net_id"],
                                    compute_id,
                                    ip['ip_address'],
                                    ip_id=port["port_id"],
                                    mac=port['mac_addr'],
                                    state=port["port_state"])

    def delete_port(self, req, compute_id, ip_id):
        """Delete a port to the subnet

        Returns the port information

        :param req: the incoming network
        :param compute_id: compute id
        :param ip_id: ip id
        """
        path = "servers/%s/os-interface" % compute_id
        tenant_id = self.tenant_from_req(req)
        path = "/%s/%s/%s" % (tenant_id, path, ip_id)
        os_req = self._get_req(req, path=path, method="DELETE")
        os_req.get_response(self.app)
        return []

        raise exception.LinkNotFound(
            "Interface %s not found" % ip_id
        )

    def get_network_id(self, req, mac, server_id):
        """Get the Network ID from the mac port

        :param req: the incoming network
        :param mac: mac port
        :param server_id: server id
        """
        ports = self._get_ports(req, server_id)
        for p in ports:
            server_mac = p['mac_addr']
            if server_mac == mac:
                return p['net_id']

        raise webob.exc.HTTPNotFound

    def assign_floating_ip(self, req, network_id, device_id,
                           pool=None):
        """assign floating ip to a server

        :param req: the incoming request
        :param network_id: network id
        :param device_id: device id
        """
        # net_id it is not needed if
        # there is just one port of the VM
        # FIXME(jorgesece): raise an error if the first port has
        # already a floating-ip
        ip = self.allocate_floating_ip(req, pool)
        # Add it to server
        self.associate_floating_ip(req, device_id, ip["ip"])

        try:
            link_public = self._build_link(
                network_id,
                device_id,
                ip["ip"],
                ip_id=ip["id"],
                pool=ip["pool"])
        except Exception:
            raise exception.OCCIInvalidSchema()
        return link_public

    @staticmethod
    def _build_networks(networks):
        ooi_net_list = []
        for net in networks:
            # TODO(jorgesece): manage IP_v6
            ooi_net = {}
            ooi_net["address"] = net.get("cidr", None)
            ooi_net["state"] = "active"
            ooi_net["id"] = net["id"]
            ooi_net["name"] = net.get("label", None)
            ooi_net["gateway"] = net.get("gateway", None)
            ooi_net_list.append(ooi_net)
        return ooi_net_list

    def list_networks(self, req):
        """Get a list of servers for a tenant.

        :param req: the incoming request
        :param parameters: parameters with tenant
        """
        path = "os-networks"
        tenant_id = self.tenant_from_req(req)
        path = "/%s/%s" % (tenant_id, path)
        os_req = self._get_req(req, path=path,
                               method="GET")
        response = os_req.get_response(self.app)
        nets = self.get_from_response(response, "networks", [])
        ooi_networks = self._build_networks(nets)
        pools = self.get_floating_ip_pools(req)
        if pools:
            net = {'id': os_helpers.PUBLIC_NETWORK,
                   'label': os_helpers.PUBLIC_NETWORK}
            public_net = self._build_networks([net])[0]
            ooi_networks.append(public_net)
        return ooi_networks

    def get_network_details(self, req, id):
        """Get info from a network.

        It returns json code from the server

        :param req: the incoming network
        :param id: net identification
        """
        if id == os_helpers.PUBLIC_NETWORK:
            net = {'id': os_helpers.PUBLIC_NETWORK,
                   'label': 'PUBLIC_to_associate_Floating_IPs'}
        else:
            path = "os-networks/%s" % id
            tenant_id = self.tenant_from_req(req)
            path = "/%s/%s" % (tenant_id, path)
            os_req = self._get_req(req, path=path,
                                   method="GET")
            response = os_req.get_response(self.app)
            net = self.get_from_response(response, "network", {})
        ooi_networks = self._build_networks([net])
        return ooi_networks[0]

    def create_network(self, req, name, cidr,
                       gateway=None, ip_version=None):
        """Create a network in nova-network.

        :param req: the incoming request
        :param name: network resource to manage
        :param cidr: parameters with values
        :param gateway: gateway ip
        :param ip_version: ip version
        """
        net_param = {'label': name,
                     'cidr': cidr,
                     'gateway': gateway
                     }
        path = "os-networks"
        tenant_id = self.tenant_from_req(req)
        path = "/%s/%s" % (tenant_id, path)
        body = utils.make_body('network', net_param)
        os_req = self._get_req(req, path=path,
                               content_type="application/json",
                               body=json.dumps(body), method="POST")
        response = os_req.get_response(self.app)
        net = self.get_from_response(
            response, "network", {})
        ooi_net = self._build_networks([net])
        return ooi_net[0]

    def delete_network(self, req, id):
        """Delete a network.

        It returns json code from the server

        :param req: the incoming network
        :param id: net identification
        :param parameters: parameters with tenant
        """
        path = "os-networks"
        tenant_id = self.tenant_from_req(req)
        path = "/%s/%s/%s" % (tenant_id, path, id)
        os_req = self._get_req(req, path=path, method="DELETE")
        os_req.get_response(self.app)
        return []
