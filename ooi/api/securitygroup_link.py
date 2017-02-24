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

from ooi.api import base
import ooi.api.helpers
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import compute
from ooi.occi.infrastructure import securitygroup
from ooi.occi.infrastructure import securitygroup_link
from ooi.occi import validator as occi_validator


def _get_security_link_resources(link_list):
    """Create OCCI security group instances from a list

    :param link_list: provides by the cloud infrastructure
    """
    occi_secgropu_resources = []
    if link_list:
        for l in link_list:
            compute_id = l['compute_id']
            sec = l['securitygroup']
            sec_id = sec.get("id")
            sec_name = sec.get("title", "")
            sec_rules = sec.get("rules", [])
            s = securitygroup.SecurityGroupResource(title=sec_name,
                                                    id=sec_id,
                                                    rules=sec_rules)
            c = compute.ComputeResource(title="Compute",
                                        id=compute_id
                                        )
            link = securitygroup_link.SecurityGroupLink(source=c,
                                                        target=s)
            occi_secgropu_resources.append(link)
    return occi_secgropu_resources


class Controller(base.Controller):

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        # TODO(jorgesece): add neutron controller to list securitygroups
        self.os_helper = ooi.api.helpers.OpenStackHelper(
            self.app,
            self.openstack_version
        )

    def _get_attachment_from_id(self, req, attachment_id):
        try:
            server_id, security_id = attachment_id.split('_', 1)
            return {"server_id": server_id,
                    "securitygroup_id": security_id}
        except ValueError:
            raise exception.LinkNotFound(link_id=attachment_id)

    def index(self, req):
        """List security group links

        :param req: request object
        """
        link_list = self.os_helper.list_server_security_links(req)
        occi_link_resources = _get_security_link_resources(link_list)
        return collection.Collection(resources=occi_link_resources)

    def show(self, req, id):
        """Get security group details

        :param req: request object
        :param id: security group identification
        """
        try:
            link_info = self._get_attachment_from_id(req, id)
            server_id = link_info["server_id"]
            security_name = link_info["securitygroup_id"]
            link = self.os_helper.get_server_security_link(
                req, server_id, security_name
            )
            occi_instance = _get_security_link_resources(
                link
            )[0]
            return occi_instance
        except Exception:
            raise exception.LinkNotFound(link_id=id)

    def create(self, req, body=None):
        """Create a security group link

        Creates a link between a server and a securitygroup.

        :param req: request object
        :param body: body request (not used)
        """
        parser = req.get_parser()(req.headers, req.body)
        scheme = {
            "category": securitygroup_link.SecurityGroupLink.kind,
        }
        obj = parser.parse()
        validator = occi_validator.Validator(obj)
        validator.validate(scheme)
        attrs = obj.get("attributes", {})
        _, securitygroup_id = ooi.api.helpers.get_id_with_kind(
            req,
            attrs.get("occi.core.target"),
            securitygroup.SecurityGroupResource.kind)
        _, server_id = ooi.api.helpers.get_id_with_kind(
            req,
            attrs.get("occi.core.source"),
            compute.ComputeResource.kind)
        self.os_helper.create_server_security_link(
            req, server_id,
            securitygroup_id)
        link = {"compute_id": server_id,
                "securitygroup": {"id": securitygroup_id}
                }
        occi_instance = _get_security_link_resources([link])
        return collection.Collection(resources=occi_instance)

    def delete(self, req, id):
        """Delete security group link

        :param req: current request
        :param id: identification
        """
        link_info = self._get_attachment_from_id(req, id)
        server_id = link_info["server_id"]
        security_id = link_info["securitygroup_id"]
        try:
            self.os_helper.delete_server_security_link(
                req, server_id, security_id)
        except Exception:
            raise exception.LinkNotFound(link_id=id)
        return []