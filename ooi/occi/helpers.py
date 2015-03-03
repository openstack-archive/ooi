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

import urlparse

_PREFIX = "http://schemas.ogf.org/occi/"


def build_schema(category):
    category = "%s#" % category
    return urlparse.urljoin(_PREFIX, category)


def check_type(obj_list, obj_type):
    if not isinstance(obj_list, (list, tuple)):
        raise TypeError('must be a list or tuple of objects')

    if not all([isinstance(i, obj_type) for i in obj_list]):
        raise TypeError('object must be of class %s' % obj_type)
