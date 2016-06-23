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


class Collection(object):
    """An OCCI Collection is used to render a set of OCCI objects.

    Depending on the rendering and the contents of the collection, there will
    be one output or another.  This class should do the magic and render the
    proper information, taking into account what is in the collection.
    """
    def __init__(self, kinds=None, mixins=None, actions=None,
                 resources=None, links=None):
        if kinds is None:
            kinds = []
        self.kinds = kinds
        if mixins is None:
            mixins = []
        self.mixins = mixins
        if actions is None:
            actions = []
        self.actions = actions
        if resources is None:
            resources = []
        self.resources = resources
        if links is None:
            links = []
        self.links = links
