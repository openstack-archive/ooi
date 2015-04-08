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
    attributes = attr.AttributeCollection(["occi.compute.architecture",
                                           "occi.compute.cores",
                                           "occi.compute.hostname",
                                           "occi.compute.speed",
                                           "occi.compute.memory",
                                           "occi.compute.state"])
    actions = (start, stop, restart, suspend)
    kind = kind.Kind(helpers.build_scheme('infrastructure'), 'compute',
                     'compute resource', attributes, 'compute/',
                     actions=actions,
                     related=[resource.Resource.kind])

    def __init__(self, title, summary=None, id=None, architecture=None,
                 cores=None, hostname=None, speed=None, memory=None,
                 state=None, mixins=[]):

        super(ComputeResource, self).__init__(title, mixins, summary=summary,
                                              id=id)

        self.attributes["occi.compute.architecture"] = attr.MutableAttribute(
            "occi.compute.architecture", architecture)
        self.attributes["occi.compute.cores"] = attr.MutableAttribute(
            "occi.compute.cores", cores)
        self.attributes["occi.compute.hostname"] = attr.MutableAttribute(
            "occi.compute.hostname", hostname)
        self.attributes["occi.compute.speed"] = attr.MutableAttribute(
            "occi.compute.speed", speed)
        self.attributes["occi.compute.memory"] = attr.MutableAttribute(
            "occi.compute.memory", memory)
        self.attributes["occi.compute.state"] = attr.InmutableAttribute(
            "occi.compute.state", state)

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
    def speed(self):
        return self.attributes["occi.compute.speed"].value

    @speed.setter
    def speed(self, value):
        self.attributes["occi.compute.speed"].value = value

    @property
    def memory(self):
        return self.attributes["occi.compute.memory"].value

    @memory.setter
    def memory(self, value):
        self.attributes["occi.compute.memory"].value = value

    @property
    def state(self):
        return self.attributes["occi.compute.state"].value
