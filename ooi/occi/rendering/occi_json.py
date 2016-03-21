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

import abc
import json

import six
import webob.exc

from ooi.occi.core import action
from ooi.occi.core import attribute
from ooi.occi.core import collection
from ooi.occi.core import kind
from ooi.occi.core import link
from ooi.occi.core import mixin
from ooi.occi.core import resource
from ooi import utils


@six.add_metaclass(abc.ABCMeta)
class JsonRenderer(object):
    def __init__(self, obj):
        self.obj = obj

    def _actions(self, env={}):
        if self.obj.actions:
            actions = []
            for a in self.obj.actions:
                actions.append(a.type_id)
            if actions:
                return {"actions": actions}
        return {}

    @abc.abstractmethod
    def render_dict(self, env={}):
        raise NotImplementedError("%s for %s object not implemented" %
                                  (type(self), type(self.obj)))

    def render(self, env={}):
        return json.dumps(self.render_dict(env))


class AttributeRenderer(JsonRenderer):
    attr_type_names = {
        attribute.AttributeType.string_type: "string",
        attribute.AttributeType.number_type: "number",
        attribute.AttributeType.boolean_type: "boolean",
        attribute.AttributeType.list_type: "array",
        attribute.AttributeType.hash_type: "object",
        # objects are represented as strings
        attribute.AttributeType.object_type: "string",
    }

    def render_dict(self, env={}):
        r = {
            "mutable": isinstance(self.obj, attribute.MutableAttribute),
            "required": self.obj.required,
            "type": self.attr_type_names[self.obj.attr_type],
        }
        if self.obj.description:
            r["description"] = self.obj.description
        if self.obj.default:
            r["default"] = self.obj.default
        # TODO(enolfc): missing pattern
        return {self.obj.name: r}


class CategoryRenderer(JsonRenderer):
    def _location(self, env={}):
        if getattr(self.obj, "location"):
            url = env.get("application_url", "")
            return {"location": utils.join_url(url, self.obj.location)}
        return {}

    def _attributes(self, env={}):
        attrs = {}
        for a in self.obj.attributes or []:
            r = AttributeRenderer(self.obj.attributes[a])
            attrs.update(r.render_dict(env))
        if attrs:
            return {"attributes": attrs}
        return {}

    def render_dict(self, env={}):
        r = {
            "term": self.obj.term,
            "scheme": self.obj.scheme,
        }
        if self.obj.title is not None:
            r["title"] = self.obj.title
        r.update(self._attributes(env))
        r.update(self._location(env))
        r.update(self._actions(env))
        return r


class KindRenderer(CategoryRenderer):
    def render_dict(self, env={}):
        r = super(KindRenderer, self).render_dict(env)
        if self.obj.parent:
            r["parent"] = self.obj.parent.type_id
        return r


class MixinRenderer(CategoryRenderer):
    def render_dict(self, env={}):
        r = super(MixinRenderer, self).render_dict(env)
        for rel_name in ("depends", "applies"):
            rel = getattr(self.obj, rel_name, [])
            if rel:
                r[rel_name] = [o.type_id for o in rel]
        return r


class EntityRenderer(JsonRenderer):
    def _mixins(self, env={}):
        mixins = []
        for m in self.obj.mixins:
            mixins.append(m.type_id)
        if mixins:
            return {"mixins": mixins}
        return {}

    def _attributes(self, env={}):
        attrs = {}
        skipped_attributes = [
            "occi.core.id",
            "occi.core.title",
            "occi.core.summary",
            "occi.core.source",
            "occi.core.target",
        ]
        for attr_name in self.obj.attributes or {}:
            if attr_name in skipped_attributes:
                continue
            if self.obj.attributes[attr_name].value is None:
                continue
            attrs[attr_name] = self.obj.attributes[attr_name].value
        if attrs:
            return {"attributes": attrs}
        return {}

    def render_dict(self, env={}):
        r = {
            "kind": self.obj.kind.type_id,
            "id": self.obj.id,
        }
        if self.obj.mixins:
            r["mixins"] = [m for m in self.obj.mixins]
        if self.obj.title is not None:
            r["title"] = self.obj.title
        r.update(self._mixins(env))
        r.update(self._attributes(env))
        r.update(self._actions(env))
        return r


class ResourceRenderer(EntityRenderer):
    def _links(self, env={}):
        links = []
        for l in self.obj.links:
            r = LinkRenderer(l)
            links.append(r.render_dict(env))
        if links:
            return {"links": links}
        else:
            return {}

    def render_dict(self, env={}):
        r = super(ResourceRenderer, self).render_dict(env)
        r.update(self._links(env))
        if self.obj.summary is not None:
            r["summary"] = self.obj.summary
        return r


class LinkRenderer(EntityRenderer):
    def render_dict(self, env={}):
        r = super(LinkRenderer, self).render_dict(env)
        url = env.get("application_url", "")
        r["source"] = {
            "kind": self.obj.source.kind.type_id,
            "location": utils.join_url(url, self.obj.source.location),
        }
        r["target"] = {
            "kind": self.obj.target.kind.type_id,
            "location": utils.join_url(url, self.obj.target.location),
        }
        return r


class ActionRenderer(CategoryRenderer):
    def _location(self, env={}):
        return {}

    def _actions(self, env={}):
        return {}


class CollectionRenderer(JsonRenderer):
    def render_dict(self, env={}):
        r = {}
        for what in ["kinds", "mixins", "actions", "resources", "links"]:
            coll = getattr(self.obj, what)
            if coll:
                r[what] = [get_renderer(obj).render_dict(env) for obj in coll]
        return r


class ExceptionRenderer(JsonRenderer):
    def render_dict(self, env={}):
        return {
            "code": self.obj.status_code,
            "message": self.obj.explanation,
        }


_MAP = {
    "action": ActionRenderer,
    "attribute": AttributeRenderer,
    "kind": KindRenderer,
    "mixin": MixinRenderer,
    "collection": CollectionRenderer,
    "resource": ResourceRenderer,
    "link": LinkRenderer,
    "exception": ExceptionRenderer,
    None: JsonRenderer,
}


def get_renderer(obj):
    if isinstance(obj, action.Action):
        type_ = "action"
    elif isinstance(obj, attribute.Attribute):
        type_ = "attribute"
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
