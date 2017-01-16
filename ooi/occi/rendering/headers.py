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
from ooi.occi.core import entity
from ooi.occi.core import kind
from ooi.occi.core import link
from ooi.occi.core import mixin
from ooi.occi.core import resource
from ooi import utils


class HeaderRenderer(object):
    def __init__(self, obj):
        self.obj = obj

    def render(self, env={}):
        raise NotImplementedError("%s for %s object not implemented" %
                                  (type(self), type(self.obj)))


class ExceptionRenderer(HeaderRenderer):
    def render(self, env={}):
        return [("X-OCCI-Error", self.obj.explanation)]


class CategoryRenderer(HeaderRenderer):
    def _render_location(self, env={}):
        if getattr(self.obj, 'location'):
            url = env.get("application_url", "")
            loc = utils.join_url(url, self.obj.location)
            return ['location="%s"' % loc]
        return []

    def _render_rel(self, env={}):
        return []

    def render(self, env={}):
        d = {
            "term": self.obj.term,
            "scheme": self.obj.scheme,
            "class": self.obj.occi_class,
            "title": self.obj.title
        }
        ret = []
        ret.append(('%(term)s; scheme="%(scheme)s"; class="%(class)s"; '
                    'title="%(title)s"') % d)
        ret.extend(self._render_rel(env))
        ret.extend(self._render_location(env))
        # FIXME(enolfc): missing attributes and actions
        return [('Category', "; ".join(ret))]


class KindRenderer(CategoryRenderer):
    def _render_rel(self, env={}):
        parent = getattr(self.obj, 'parent', None)
        if parent is not None:
            d = {"scheme": parent.scheme, "term": parent.term}
            return ['rel="%(scheme)s%(term)s"' % d]
        return []


class ActionRenderer(CategoryRenderer):
    def _render_location(self, env={}):
        """Do not render location for actions."""
        return []

    def render(self, ass_obj=None, env={}):
        # We have an associated object, render it as a link to that object
        if ass_obj is not None:
            url = env.get("application_url", "")
            term = ass_obj.kind.term + "/"
            url = utils.join_url(url, [term, ass_obj.id, self.obj.location])
            d = {"location": url,
                 "rel": self.obj.type_id}
            l = '<%(location)s>; rel="%(rel)s"' % d
            return [('Link', l)]
        else:
            # Otherwise, render as category
            return super(ActionRenderer, self).render(env=env)


class MixinRenderer(CategoryRenderer):
    # See OCCI 1.2 text rendering 5.5.2 Mixin Instance Attribute Rendering
    # Specifics: only render as "rel" the first "depends" of mixin
    def _render_rel(self, env={}):
        depends = getattr(self.obj, 'depends', [])
        if depends:
            d = {"scheme": depends[0].scheme, "term": depends[0].term}
            return ['rel="%(scheme)s%(term)s"' % d]
        return []


class CollectionRenderer(HeaderRenderer):
    def render(self, env={}):
        ret = []
        contents = (self.obj.kinds, self.obj.mixins, self.obj.actions,
                    self.obj.resources, self.obj.links)
        # Render individual objects if there are more that one type of objects
        # otherwise render as X-OCCI-Location headers
        if len([x for x in contents if x]) > 1:
            for what in contents:
                for el in what:
                    renderer = get_renderer(el)
                    ret.extend(renderer.render(env=env))
        else:
            app_url = env.get("application_url", "")
            for what in contents:
                for el in what:
                    url = utils.join_url(app_url, el.location)
                    ret.append(('X-OCCI-Location', '%s' % url))
        return ret


class AttributeRenderer(HeaderRenderer):
    def render_attr(self, env={}):
        value_str = ''
        if isinstance(self.obj.value, six.string_types):
            value_str = '"%s"' % self.obj.value
        elif isinstance(self.obj.value, bool):
            value_str = '"%s"' % str(self.obj.value).lower()
        elif isinstance(self.obj.value, entity.Entity):
            app_url = env.get("application_url", "")
            url = utils.join_url(app_url, self.obj.value.location)
            value_str = '"%s"' % url
        else:
            value_str = "%s" % self.obj.value
        return '%s=%s' % (self.obj.name, value_str)

    def render(self, env={}):
        return [('X-OCCI-Attribute', self.render_attr(env))]


class EntityRenderer(HeaderRenderer):
    def render(self, env={}):
        ret = []
        ret.extend(KindRenderer(self.obj.kind).render(env=env))
        for m in self.obj.mixins:
            ret.extend(MixinRenderer(m).render(env=env))
        for a in self.obj.attributes:
            # FIXME(aloga): I dont like this test here
            if self.obj.attributes[a].value is None:
                continue
            r = AttributeRenderer(self.obj.attributes[a])
            ret.extend(r.render(env=env))
        return ret


class LinkRenderer(EntityRenderer):
    def render_link(self, env={}):
        ret = []
        url = env.get("application_url", "")
        url = utils.join_url(url, self.obj.location)
        d = {"location": url,
             "scheme": self.obj.target.kind.scheme,
             "term": self.obj.target.kind.term,
             "self": url}
        l = '<%(location)s>; rel="%(scheme)s%(term)s"; self="%(self)s"' % d
        ret.append(l)
        categories = [self.obj.kind.type_id]
        for m in self.obj.mixins:
            categories.append(m.type_id)
        ret.append('category="%s"' % ' '.join(categories))
        for a in self.obj.attributes:
            if self.obj.attributes[a].value is None:
                continue
            ret.append(AttributeRenderer(
                self.obj.attributes[a]).render_attr(env=env))
        return [('Link', '; '.join(ret))]


class ResourceRenderer(EntityRenderer):
    def render(self, env={}):
        ret = super(ResourceRenderer, self).render(env)
        if self.obj.actions:
            for a in self.obj.actions:
                r = ActionRenderer(a)
                ret.extend(r.render(ass_obj=self.obj, env=env))
        for l in self.obj.links:
            ret.extend(LinkRenderer(l).render_link(env=env))
        return ret


_MAP = {
    "action": ActionRenderer,
    "kind": KindRenderer,
    "mixin": MixinRenderer,
    "collection": CollectionRenderer,
    "resource": ResourceRenderer,
    "link": LinkRenderer,
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
    elif isinstance(obj, link.Link):
        type_ = "link"
    elif isinstance(obj, webob.exc.HTTPException):
        type_ = "exception"
    else:
        type_ = None
    return _MAP.get(type_)(obj)
