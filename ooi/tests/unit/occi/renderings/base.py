# Copyright 2016 Spanish National Research Council
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

import uuid

import webob.exc

from ooi.occi.core import action
from ooi.occi.core import attribute
from ooi.occi.core import collection
from ooi.occi.core import kind
from ooi.occi.core import link
from ooi.occi.core import mixin
from ooi.occi.core import resource
import ooi.tests.base


class BaseRendererTest(ooi.tests.base.TestCase):
    def get_render_and_assert(self, obj, observed=None):
        if observed is None:
            r = self.renderer.get_renderer(obj)
            observed = r.render()

        if isinstance(obj, action.Action):
            self.assertAction(obj, observed)
        elif isinstance(obj, collection.Collection):
            self.assertCollection(obj, observed)
        elif isinstance(obj, kind.Kind):
            self.assertKind(obj, observed)
        elif isinstance(obj, link.Link):
            self.assertLink(obj, observed)
        elif isinstance(obj, mixin.Mixin):
            self.assertMixin(obj, observed)
        elif isinstance(obj, resource.Resource):
            self.assertResource(obj, observed)
        elif isinstance(obj, webob.exc.HTTPException):
            self.assertException(obj, observed)

    def test_action(self):
        act = action.Action("scheme", "term", "title")
        self.get_render_and_assert(act)

    def test_collection_resources(self):
        r1 = resource.Resource("foo", [], uuid.uuid4().hex)
        r2 = resource.Resource("bar", [], uuid.uuid4().hex)
        c = collection.Collection(resources=[r1, r2])
        self.get_render_and_assert(c)

    def test_mixed_collection(self):
        res = resource.Resource("foo", [], uuid.uuid4().hex)
        knd = kind.Kind("scheme", "term", "title")
        c = collection.Collection(kinds=[knd], resources=[res])
        r = self.renderer.get_renderer(c)
        observed = r.render()
        self.assertMixedCollection(knd, res, observed)

    def test_exception(self):
        exc = webob.exc.HTTPBadRequest()
        self.get_render_and_assert(exc)

    def test_kind(self):
        knd = kind.Kind("scheme", "term", "title")
        self.get_render_and_assert(knd)

    def test_kind_attributes(self):
        attr = attribute.MutableAttribute("org.example", "foo",
                                          description="bar",
                                          default="baz")
        knd = kind.Kind("scheme", "term", "title",
                        attributes=attribute.AttributeCollection({
                            "org.example": attr}
                        ))
        r = self.renderer.get_renderer(knd)
        observed = r.render()
        self.assertKindAttr(knd, attr, observed)

    def test_mixin(self):
        mxn = mixin.Mixin("scheme", "term", "title")
        self.get_render_and_assert(mxn)

    def test_link(self):
        r1 = resource.Resource(None, [])
        r2 = resource.Resource(None, [])
        lnk = link.Link("title", [], r1, r2, "id")
        self.get_render_and_assert(lnk)

    def test_resource(self):
        res = resource.Resource("title", [], "foo", "summary")
        self.get_render_and_assert(res)

    def test_resource_mixins(self):
        mixins = [
            mixin.Mixin("foo", "bar", None),
            mixin.Mixin("baz", "foobar", None),
        ]
        res = resource.Resource("title", mixins, "foo", "summary")
        r = self.renderer.get_renderer(res)
        observed = r.render()
        self.assertResourceMixins(res, mixins, observed)

    def test_resource_actions(self):
        actions = [
            action.Action("foo", "bar", None),
            action.Action("baz", "foobar", None),
        ]
        res = resource.Resource("title", [], "foo", "summary")
        res.actions = actions
        r = self.renderer.get_renderer(res)
        observed = r.render()
        self.assertResourceActions(res, actions, observed)

    def test_resource_string_attr(self):
        res = resource.Resource("title", [], "foo", "summary")
        attr = ("org.example.str", "baz")
        res.attributes[attr[0]] = attribute.MutableAttribute(attr[0], attr[1])
        r = self.renderer.get_renderer(res)
        observed = r.render()
        self.assertResourceStringAttr(res, attr, observed)

    def test_resource_int_attr(self):
        res = resource.Resource("title", [], "foo", "summary")
        attr = ("org.example.int", 465)
        res.attributes[attr[0]] = attribute.MutableAttribute(attr[0], attr[1])
        r = self.renderer.get_renderer(res)
        observed = r.render()
        self.assertResourceIntAttr(res, attr, observed)

    def test_resource_bool_attr(self):
        res = resource.Resource("title", [], "foo", "summary")
        attr = ("org.example.bool", True)
        res.attributes[attr[0]] = attribute.MutableAttribute(attr[0], attr[1])
        r = self.renderer.get_renderer(res)
        observed = r.render()
        self.assertResourceBoolAttr(res, attr, observed)

    def test_resource_link(self):
        r1 = resource.Resource(None, [])
        r2 = resource.Resource(None, [])
        r1.link(r2)
        r = self.renderer.get_renderer(r1)
        observed = r.render()
        self.assertResourceLink(r1, r2, observed)

    def test_resource_link_with_mixins(self):
        r1 = resource.Resource(None, [])
        r2 = resource.Resource(None, [])
        r1.link(r2, [mixin.Mixin("s1", "term", "title"),
                     mixin.Mixin("s2", "term", "title")])
        r = self.renderer.get_renderer(r1)
        observed = r.render()
        self.assertResourceLink(r1, r2, observed)
