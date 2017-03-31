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
from ooi.api import helpers
from ooi.api import helpers_neutron
from ooi import exception
from ooi.occi.core import collection
from ooi.occi.infrastructure import securitygroup
from ooi.occi import validator as occi_validator


def parse_validate_schema(req, scheme=None,
                          required_attr=None):
    """Parse attributes and validate scheme


    Returns attributes from request
    If scheme is specified, it validates the OCCI scheme:
     -Raises exception in case of being invalid

    :param req: request
    :param: scheme: scheme to validate
    :param: required_attr: attributes required
    """
    parser = req.get_parser()(req.headers, req.body.decode("utf8"))
    if scheme:
        attributes = parser.parse()
        validator = occi_validator.Validator(attributes)
        validator.validate(scheme)
        validator.validate_attributes(required_attr)
    else:
        attributes = parser.parse_attributes(req.headers)
    return attributes


def process_parameters(req, scheme=None,
                       required_attr=None):
    """Get attributes from request parameters

    :param req: request
    :param scheme: scheme to validate
    :param required_attr: attributes required
    """
    parameters = parse_validate_schema(req, scheme, required_attr)
    try:
        attributes = {}
        if 'X_PROJECT_ID' in req.headers:
            attributes["X_PROJECT_ID"] = req.headers["X_PROJECT_ID"]
        if "attributes" in parameters:
            for k, v in parameters.get("attributes", None).items():
                attributes[k.strip()] = v
        if not attributes:
            attributes = None
    except Exception:
        raise exception.Invalid
    return attributes


class Controller(base.Controller):
    def __init__(self, app=None, openstack_version=None,
                 neutron_ooi_endpoint=None):
        """Security group controller initialization

        :param app: application
        :param: openstack_version: nova version
        :param: neutron_ooi_endpoint: This parameter
        indicates the Neutron endpoint to load the Neutron Helper.
        If it is None, Nova api is used.
        """

        super(Controller, self).__init__(
            app=app,
            openstack_version=openstack_version)
        if neutron_ooi_endpoint:
            self.os_helper = helpers_neutron.OpenStackNeutron(
                neutron_ooi_endpoint
            )
        else:
            self.os_helper = helpers.OpenStackHelper(
                self.app,
                self.openstack_version
            )

    @staticmethod
    def _get_security_group_resources(securitygroup_list):
        """Create OCCI security group instances from list

        :param securitygroup_list: security group objects
        provides by the cloud infrastructure
        :return occi security group list
        """
        occi_securitygroup_resources = []
        if securitygroup_list:
            for s in securitygroup_list:
                s_rules = s['rules']
                s_id = s["id"]
                s_name = s["title"]
                s_summary = s["summary"]
                s = securitygroup.SecurityGroupResource(title=s_name,
                                                        id=s_id,
                                                        rules=s_rules,
                                                        summary=s_summary)
                occi_securitygroup_resources.append(s)
        return occi_securitygroup_resources

    def index(self, req):
        """List security groups

        :param req: request object
        """
        occi_sc = self.os_helper.list_security_groups(req)
        occi_sc_resources = self._get_security_group_resources(
            occi_sc)

        return collection.Collection(
            resources=occi_sc_resources)

    def show(self, req, id):
        """Get security group details

        :param req: request object
        :param id: security group identification
        """
        resp = self.os_helper.get_security_group_details(req, id)
        occi_sc_resources = self._get_security_group_resources(
            [resp])
        return occi_sc_resources[0]

    def create(self, req, body=None):
        """Create a network instance in the cloud

        :param req: request object
        :param body: body request (not used)
        """
        scheme = {
            "category": securitygroup.SecurityGroupResource.kind,
        }
        required = ["occi.core.title",
                    "occi.securitygroup.rules"
                    ]
        attributes = process_parameters(req, scheme, required)
        name = attributes.get('occi.core.title')
        description = attributes.get("occi.core.summary", "")
        try:
            rules = attributes.get('occi.securitygroup.rules')
        except Exception:
            raise exception.Invalid(
                "Bad JSON format for occi.securitygroup.rules: %s"
                % attributes.get(
                    'occi.securitygroup.rules'))
        sec = self.os_helper.create_security_group(
            req, name, description, rules
        )
        occi_sec_resources = self._get_security_group_resources([sec])
        return collection.Collection(
            resources=occi_sec_resources)

    def delete(self, req, id):
        """delete security groups which satisfy the parameters

        :param req: current request
        :param id: identification
        """
        response = self.os_helper.delete_security_group(req, id)
        return response

    def run_action(self, req, id, body):
        """Run action over the security group

        :param req: current request
        :param id: security group
        :param body: body
        """
        action = req.GET.get("action", None)
        occi_actions = [a.term for a in
                        securitygroup.SecurityGroupResource.actions]

        if action is None or action not in occi_actions:
            raise exception.InvalidAction(action=action)
        raise exception.NotImplemented("Security group actions are not implemented")