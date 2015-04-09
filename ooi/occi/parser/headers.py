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

import shlex

#from ooi import exception


def _lexize(s, separator, ignore_whitespace=False):
    lex = shlex.shlex(instream=s, posix=True)
    lex.commenters = ""
    if ignore_whitespace:
        lex.whitespace = separator
    else:
        lex.whitespace += separator
    lex.whitespace_split = True
    return list(lex)


class HeaderParser(object):
    # TODO(enolfc): invalid input will crash this function!
    def parse(self, headers):
        obj = {
            "kind": None,
            "mixins": [],
            "attributes": {},
        }
        for ctg in _lexize(headers["Category"],
                           separator=",",
                           ignore_whitespace=True):
            ll = _lexize(ctg, ";")
            d = {"term": ll[0]}  # assumes 1st element => term's value
            d.update(dict([i.split('=') for i in ll[1:]]))
            ctg_class = d.get("class", None)
            ctg_type = '%(scheme)s%(term)s' % d
            if ctg_class == "kind":
                if obj.get("kind") is not None:
                    # TODO(enolfc): use a better exception
                    #raise exception.HeaderValidation()
                    raise Exception("Two kinds in an object??")
                obj["kind"] = ctg_type
            elif ctg_class == "mixin":
                obj["mixins"].append(ctg_type)
        for attr in _lexize(headers["X-OCCI-Attribute"],
                            separator=",",
                            ignore_whitespace=True):
            n, v = attr.split('=', 1)
            ns = n.strip().split('.')
            d = obj["attributes"]
            for s in ns[:-1]:
                try:
                    d = d[s]
                except KeyError:
                    d[s] = {}
                    d = d[s]
            d[ns[-1]] = v
        print obj


#hdrs = {
#    "Category": 'compute;scheme="http://schemas.ogf.org/occi/infrastructure#";class="kind",foo;scheme="http://schemas.openstack.org/template/resource#";class="mixin",bar;scheme="http://schemas.openstack.org/template/os#";class="mixin",user_data;scheme="http://schemas.openstack.org/compute/instance#";class="mixin"',
#    "X-OCCI-Attribute": 'occi.core.id="1234", occi.core.size=12, occi.core.bool="true", occi.core.shitty="1234 234"'
#}
#
#parser = HeaderParser()
#parser.parse(hdrs)
