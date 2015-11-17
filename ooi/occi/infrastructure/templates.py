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

from ooi.occi.core import mixin
from ooi.occi import helpers


class OCCIOSTemplate(mixin.Mixin):
    scheme = helpers.build_scheme("infrastructure")
    _location = "os_tpl"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", self._location + "/")
        super(OCCIOSTemplate, self).__init__(self.scheme, *args, **kwargs)


os_tpl = OCCIOSTemplate("os_tpl",
                        "OCCI OS Template")


class OCCIResourceTemplate(mixin.Mixin):
    scheme = helpers.build_scheme("infrastructure")
    _location = "resource_tpl"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("location", self._location + "/")
        super(OCCIResourceTemplate, self).__init__(self.scheme,
                                                   *args,
                                                   **kwargs)


resource_tpl = OCCIResourceTemplate("resource_tpl",
                                    "OCCI Resource Template")
