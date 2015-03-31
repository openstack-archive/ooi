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

import six
import webob.exc

from ooi.occi.core import action
from ooi.occi.core import collection
from ooi.occi.core import kind
from ooi.occi.core import mixin
from ooi.occi.core import resource


class HeaderRenderer(object):
    def __init__(self, obj):
        self.obj = obj

    def render(self, env={}):
        raise NotImplementedError("%s for %s object not implemented" %
                                  (type(self), type(self.obj)))


class ExceptionRenderer(HeaderRenderer):
    def render(self, env={}):
        return []


class CategoryRenderer(HeaderRenderer):
    def render(self, env={}):
        d = {
            "term": self.obj.term,
            "scheme": self.obj.scheme,
            "class": self.obj.occi_class
        }
        return [('Category',
                 '%(term)s; scheme="%(scheme)s"; class="%(class)s"' % d)]


class KindRenderer(CategoryRenderer):
    pass


class ActionRenderer(CategoryRenderer):
    pass


class MixinRenderer(CategoryRenderer):
    pass


class CollectionRenderer(HeaderRenderer):
    def render(self, env={}):
        app_url = env.get("application_url", "")
        ret = []
        for what in [self.obj.kinds, self.obj.mixins, self.obj.actions,
                     self.obj.resources, self.obj.links]:
            for el in what:
                url = app_url + el.location
                ret.append(('X-OCCI-Location', '%s' % url))
        return ret


class AttributeRenderer(HeaderRenderer):
    def render(self, env={}):
        value_str = ''
        if isinstance(self.obj.value, six.string_types):
            value_str = '"%s"' % self.obj.value
        elif isinstance(self.obj.value, bool):
            value_str = '"%s"' % str(self.obj.value).lower()
        else:
            value_str = "%s" % self.obj.value
        return [('X-OCCI-Attribute', '%s=%s' % (self.obj.name, value_str))]


class ResourceRenderer(HeaderRenderer):
    def render(self, env={}):
        ret = []
        ret.extend(KindRenderer(self.obj.kind).render())
        for m in self.obj.mixins:
            ret.extend(MixinRenderer(m).render())
        for a in self.obj.attributes:
            # FIXME(aloga): I dont like this test here
            if self.obj.attributes[a].value is None:
                continue
            ret.extend(AttributeRenderer(self.obj.attributes[a]).render())
        for l in self.obj.links:
            pass
            # FIXME(aloga): we need to fix this
#            ret.append(LinkRenderer(l))
        return ret


_MAP = {
    "action": ActionRenderer,
    "kind": KindRenderer,
    "mixin": MixinRenderer,
    "collection": CollectionRenderer,
    "resource": ResourceRenderer,
    "exception": ExceptionRenderer,
    None: HeaderRenderer,
}


def get_renderer(obj):
    if isinstance(obj, action.Action):
        type_ = "action"
    elif isinstance(obj, collection.Collection):
        type_ = "collection"
    elif isinstance(obj, mixin.Mixin):
        type_ = "mixin"
    elif isinstance(obj, kind.Kind):
        type_ = "kind"
    elif isinstance(obj, resource.Resource):
        type_ = "resource"
    elif isinstance(obj, webob.exc.HTTPException):
        type_ = "exception"
    else:
        type_ = None
    return _MAP.get(type_)(obj)
