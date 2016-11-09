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

from ooi.occi.core import action
from ooi.occi.core import attribute as attr
from ooi.occi.core import kind
from ooi.occi.core import resource
from ooi.occi import helpers

start = action.Action(helpers.build_scheme('infrastructure/compute/action'),
                      "start", "start compute instance")

stop = action.Action(helpers.build_scheme('infrastructure/compute/action'),
                     "stop", "stop compute instance")

restart = action.Action(helpers.build_scheme('infrastructure/compute/action'),
                        "restart", "restart compute instance")

suspend = action.Action(helpers.build_scheme('infrastructure/compute/action'),
                        "suspend", "suspend compute instance")


class ComputeResource(resource.Resource):
    attributes = attr.AttributeCollection({
        "occi.compute.architecture": attr.MutableAttribute(
            "occi.compute.architecture",
            description="CPU architecture of the instance",
            attr_type=attr.AttributeType.string_type),
        "occi.compute.cores": attr.MutableAttribute(
            "occi.compute.cores",
            description="Number of virtual cores assigned to the instance",
            attr_type=attr.AttributeType.number_type),
        "occi.compute.hostname": attr.MutableAttribute(
            "occi.compute.hostname",
            description="Fully Qualified DNS hostname for the instance",
            attr_type=attr.AttributeType.string_type),
        "occi.compute.share": attr.MutableAttribute(
            "occi.compute.share",
            description="Relative number of CPU shares for the instance",
            attr_type=attr.AttributeType.number_type),
        "occi.compute.memory": attr.MutableAttribute(
            "occi.compute.memory",
            description="Maximum RAM in gigabytes allocated to the instance",
            attr_type=attr.AttributeType.number_type),
        "occi.compute.state": attr.InmutableAttribute(
            "occi.compute.state", description="Current state of the instance",
            attr_type=attr.AttributeType.string_type),
        "occi.compute.state.message": attr.InmutableAttribute(
            "occi.compute.state.message",
            description=("Human-readable explanation of the current instance "
                         "state"),
            attr_type=attr.AttributeType.string_type),
    })

    actions = (start, stop, restart, suspend)
    kind = kind.Kind(helpers.build_scheme('infrastructure'), 'compute',
                     'compute resource', attributes, 'compute/',
                     actions=actions,
                     parent=resource.Resource.kind)

    def __init__(self, title, summary=None, id=None, architecture=None,
                 cores=None, hostname=None, share=None, memory=None,
                 state=None, message=None, mixins=[]):

        super(ComputeResource, self).__init__(title, mixins, summary=summary,
                                              id=id)

        self.architecture = architecture
        self.cores = cores
        self.hostname = hostname
        self.share = share
        self.memory = memory
        self.attributes["occi.compute.state"] = (
            attr.InmutableAttribute.from_attr(
                self.attributes["occi.compute.state"], state))
        self.attributes["occi.compute.state.message"] = (
            attr.InmutableAttribute(
                self.attributes["occi.compute.state.message"], message))

    @property
    def architecture(self):
        return self.attributes["occi.compute.architecture"].value

    @architecture.setter
    def architecture(self, value):
        self.attributes["occi.compute.architecture"].value = value

    @property
    def cores(self):
        return self.attributes["occi.compute.cores"].value

    @cores.setter
    def cores(self, value):
        self.attributes["occi.compute.cores"].value = value

    @property
    def hostname(self):
        return self.attributes["occi.compute.hostname"].value

    @hostname.setter
    def hostname(self, value):
        self.attributes["occi.compute.hostname"].value = value

    @property
    def share(self):
        return self.attributes["occi.compute.share"].value

    @share.setter
    def share(self, value):
        self.attributes["occi.compute.share"].value = value

    @property
    def memory(self):
        return self.attributes["occi.compute.memory"].value

    @memory.setter
    def memory(self, value):
        self.attributes["occi.compute.memory"].value = value

    @property
    def state(self):
        return self.attributes["occi.compute.state"].value

    @property
    def message(self):
        return self.attributes["occi.compute.state.message"].value
