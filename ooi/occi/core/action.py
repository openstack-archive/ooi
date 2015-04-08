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

from ooi.occi.core import category


class Action(category.Category):
    """OCCI Action.

    An Action represents an invocable operation applicable to a resource
    instance.
    """

    def __init__(self, scheme, term, title, attributes=None, location=None):
        super(Action, self).__init__(scheme, term, title,
                                     attributes=attributes,
                                     location="?action=%s" % term)

    def _class_name(self):
        return "action"
