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

from ooi.occi.core import attribute as attr
from ooi.occi.core import kind
from ooi.occi.core import link
from ooi.occi import helpers


class SecurityGroupLink(link.Link):
    attributes = attr.AttributeCollection({
        "occi.securitygrouplink.state": attr.InmutableAttribute(
            "occi.securitygrouplink.state",
            description="Current state of the instance",
            attr_type=attr.AttributeType.string_type)
    })
    kind = kind.Kind(helpers.build_scheme('infrastructure'),
                     'securitygrouplink', 'security group link resource',
                     attributes, 'securitygrouplink/',
                     parent=link.Link.kind)

    def __init__(self, source, target, state=None):
        link_id = '_'.join([source.id, target.id])
        super(SecurityGroupLink, self).__init__(None, [], source,
                                                target, link_id)

        self.attributes["occi.securitygrouplink.state"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.securitygrouplink.state"], state))

    @property
    def state(self):
        return self.attributes["occi.securitygrouplink.state"].value