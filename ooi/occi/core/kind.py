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
from ooi.occi.core import category
from ooi.occi import helpers


class Kind(category.Category):
    """OCCI Kind.

    The Kind type is the core of the type classification system built into the
    OCCI Core Model. Kind is a specialisation of Category and introduces
    additional resource capabilities in terms of Actions.
    """

    def __init__(self, scheme, term, title, attributes=None, location=None,
                 parent=None, actions=[]):
        super(Kind, self).__init__(scheme, term, title, attributes=attributes,
                                   location=location)

        helpers.check_single_type(parent, Kind)
        helpers.check_type(actions, action.Action)

        self.parent = parent
        self.actions = actions

    def _class_name(self):
        return "kind"
