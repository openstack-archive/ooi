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

from ooi.occi.core import attribute
from ooi.occi.core import mixin
from ooi.openstack import helpers


class OpenStackUserData(mixin.Mixin):
    scheme = helpers.build_scheme("compute/instance")
    term = "user_data"

    def __init__(self, user_data=None):
        attrs = [
            attribute.InmutableAttribute("org.openstack.compute.user_data",
                                         user_data),
        ]

        attrs = attribute.AttributeCollection({a.name: a for a in attrs})

        super(OpenStackUserData, self).__init__(
            OpenStackUserData.scheme, OpenStackUserData.term,
            "Contextualization extension - user_data",
            attributes=attrs)

    @property
    def user_data(self):
        return self.attributes["org.openstack.compute.user_data"].value


class OpenStackPublicKey(mixin.Mixin):
    scheme = helpers.build_scheme("instance/credentials")
    term = "public_key"

    def __init__(self, name=None, data=None):
        attrs = [
            attribute.InmutableAttribute(
                "org.openstack.credentials.publickey.name", name),
            attribute.InmutableAttribute(
                "org.openstack.credentials.publickey.data", data),
        ]

        attrs = attribute.AttributeCollection({a.name: a for a in attrs})

        super(OpenStackPublicKey, self).__init__(
            OpenStackPublicKey.scheme, OpenStackPublicKey.term,
            "Contextualization extension - public_key",
            attributes=attrs)

    @property
    def name(self):
        attr = "org.openstack.credentials.publickey.name"
        return self.attributes[attr].value

    @property
    def data(self):
        attr = "org.openstack.credentials.publickey.data"
        return self.attributes[attr].value


user_data = OpenStackUserData()
public_key = OpenStackPublicKey()
