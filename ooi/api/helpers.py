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

import copy
import json
import os

import six.moves.urllib.parse as urlparse

from ooi import exception
from ooi.log import log as logging
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
    try:
        message = response.json_body.popitem()[1].get("message")
    except Exception:
        LOG.exception("Unknown error happenened processing response %s"
                      % response)
        return webob.exc.HTTPInternalServerError()

    exc = exceptions.get(code, webob.exc.HTTPInternalServerError)
    return exc(explanation=message)


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
            return response.json_body.get(element, default)
        else:
            raise exception_from_response(response)


class OpenStackHelper(BaseHelper):
    """Class to interact with the nova API."""

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
                               block_device_mapping_v2=None):
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

        return self._get_req(req,
                             path=path,
                             content_type="application/json",
                             body=json.dumps(body),
                             method="POST")

    def create_server(self, req, name, image, flavor,
                      user_data=None, key_name=None,
                      block_device_mapping_v2=None):
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
            block_device_mapping_v2=block_device_mapping_v2)
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
