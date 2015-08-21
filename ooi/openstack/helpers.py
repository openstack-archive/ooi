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

from ooi.occi import helpers

_PREFIX = "http://schemas.openstack.org/"


def build_scheme(category):
    return helpers.build_scheme(category, prefix=_PREFIX)


def vm_state(nova_status):
    if nova_status == "ACTIVE":
        return "active"
    elif nova_status == "SUSPENDED":
        return "suspended"
    else:
        return "inactive"


# TODO(enolfc): Do really implement this.
def vol_state(nova_status):
    return "online"
