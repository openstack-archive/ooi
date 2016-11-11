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
from ooi.occi import helpers
from ooi.occi.infrastructure import compute


class SSHKey(mixin.Mixin):
    scheme = helpers.build_scheme("infrastructure/credentials")
    term = "ssh_key"

    def __init__(self, ssh_key=None):
        attrs = [
            attribute.MutableAttribute(
                "occi.crendentials.ssh.publickey", ssh_key, required=True,
                description=("The contents of the public key file to be "
                             "injected into the Compute Resource"),
                attr_type=attribute.AttributeType.string_type),
        ]

        attrs = attribute.AttributeCollection({a.name: a for a in attrs})

        super(SSHKey, self).__init__(SSHKey.scheme, SSHKey.term,
                                     "Credentials mixin",
                                     attributes=attrs,
                                     applies=[compute.ComputeResource.kind])

    @property
    def ssh_key(self):
        attr = "occi.crendentials.ssh.publickey"
        return self.attributes[attr].value

    @ssh_key.setter
    def ssh_key(self, value):
        attr = "occi.crendentials.ssh.publickey"
        self.attributes[attr].value = value


class UserData(mixin.Mixin):
    scheme = helpers.build_scheme("infrastructure/compute")
    term = "user_data"

    def __init__(self, user_data=None):
        attrs = [
            attribute.MutableAttribute(
                "occi.compute.userdata", user_data, required=True,
                description=("Contextualization data (e.g., script, "
                             "executable) that the client supplies once and "
                             "only once. It cannot be updated."),
                attr_type=attribute.AttributeType.string_type),
        ]

        attrs = attribute.AttributeCollection({a.name: a for a in attrs})

        super(UserData, self).__init__(UserData.scheme,
                                       UserData.term,
                                       "Contextualization mixin",
                                       attributes=attrs,
                                       applies=[compute.ComputeResource.kind])

    @property
    def user_data(self):
        attr = "occi.compute.userdata"
        return self.attributes[attr].value

    @user_data.setter
    def user_data(self, value):
        attr = "occi.compute.userdata"
        self.attributes[attr].value = value

ssh_key = SSHKey()
user_data = UserData()
